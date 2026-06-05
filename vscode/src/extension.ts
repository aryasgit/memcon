/**
 * Memcon — VS Code / Cursor extension.
 *
 * Talks to the local Memcon FastAPI (default http://localhost:8000) and
 * surfaces three of its capabilities inline in the editor:
 *
 *   • Memcon: Ask          — Cmd/Ctrl+Shift+M. Pops an input, calls /ask,
 *                            opens an untitled markdown editor with the
 *                            grounded answer + sources.
 *   • Memcon: Save         — Cmd/Ctrl+Shift+S on an editor selection. Sends
 *                            the selected text to /memory/session with the
 *                            file path as the title hint.
 *   • Memcon sidebar       — "Recent" tree in the activity bar. Clicking a
 *                            note opens its full markdown in a preview tab.
 *   • Memcon: Search       — semantic search returning raw chunks via /query.
 *   • Memcon: Open dashboard — opens the local web UI in your browser.
 */
import * as vscode from "vscode";

// ── Utilities ────────────────────────────────────────────────────────────

function getApiUrl(): string {
    const url = vscode.workspace
        .getConfiguration("memcon")
        .get<string>("apiUrl", "http://localhost:8000");
    return url.replace(/\/+$/, "");
}

function getTopK(): number {
    return vscode.workspace
        .getConfiguration("memcon")
        .get<number>("topK", 5);
}

function getRecentLimit(): number {
    return vscode.workspace
        .getConfiguration("memcon")
        .get<number>("recentLimit", 15);
}

const FETCH_TIMEOUT_MS = 15000;

async function memconFetch(
    path: string,
    init?: RequestInit,
    token?: vscode.CancellationToken
): Promise<any> {
    const url = `${getApiUrl()}${path}`;
    // Hard timeout: a slow/hung/overloaded API (the bulk-op incident) must never
    // wedge the editor — abort after FETCH_TIMEOUT_MS. Also abort if the caller's
    // CancellationToken fires (e.g. the user cancels the "thinking…" progress).
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), FETCH_TIMEOUT_MS);
    const sub = token?.onCancellationRequested(() => ctl.abort());
    let res: Response;
    try {
        res = await fetch(url, { ...init, signal: ctl.signal });
    } catch (e: any) {
        if (e?.name === "AbortError") {
            throw new Error(
                token?.isCancellationRequested
                    ? "Memcon: cancelled."
                    : `Memcon timed out after ${FETCH_TIMEOUT_MS / 1000}s — ${getApiUrl()} is slow or busy.`
            );
        }
        throw new Error(
            `Cannot reach Memcon at ${getApiUrl()}. Is it running? ` +
            `(Try: cd ~/memcon && ./start.sh — or run \`memcon serve\`)`
        );
    } finally {
        clearTimeout(timer);
        sub?.dispose();
    }
    if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(`${res.status} ${res.statusText}: ${body.slice(0, 200)}`);
    }
    try {
        return await res.json();
    } catch (e: any) {
        throw new Error(
            `Memcon returned a non-JSON response from ${url} — is "memcon.apiUrl" pointing at the API?`
        );
    }
}

function timeAgo(epoch: number): string {
    const s = Date.now() / 1000 - epoch;
    if (s < 60) return `${Math.floor(s)}s ago`;
    if (s < 3600) return `${Math.floor(s / 60)}m ago`;
    if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
    return `${Math.floor(s / 86400)}d ago`;
}

async function showMarkdown(content: string, title?: string): Promise<void> {
    const doc = await vscode.workspace.openTextDocument({
        language: "markdown",
        content,
    });
    await vscode.window.showTextDocument(doc, { preview: true });
    if (title) {
        // VS Code doesn't let us name untitled docs, but the title shows
        // briefly via setStatusBarMessage so the user knows what they got.
        vscode.window.setStatusBarMessage(`Memcon: ${title}`, 4000);
    }
}

// ── Commands ─────────────────────────────────────────────────────────────

async function ask(): Promise<void> {
    const q = await vscode.window.showInputBox({
        prompt: "Ask Memcon",
        placeHolder: "What caused the servo to overheat?",
        ignoreFocusOut: true,
    });
    if (!q || !q.trim()) return;

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: "Memcon — thinking…",
            cancellable: true,
        },
        async (_progress, token) => {
            try {
                const d = await memconFetch("/ask", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ question: q, top_k: getTopK() }),
                }, token);
                const sources = (d.sources || []).join(", ") || "—";
                // Lean mode: /ask returns no prose answer (answer: null) — render the
                // grounding chunks directly so Ask still surfaces your memory.
                let body: string;
                if (d.answer) {
                    body = d.answer;
                } else {
                    const chunks: any[] = d.raw_chunks || [];
                    body = (d.note ? `_${d.note}_\n\n` : "") + (chunks.length
                        ? chunks.map((c) => `### ${c.doc_name || "note"} · score ${c.score}\n${c.text || ""}`).join("\n\n")
                        : "(no answer)");
                }
                const content = [
                    `# ${q}`,
                    "",
                    body,
                    "",
                    "---",
                    `**Sources** · ${sources}`,
                    `**Chunks used** · ${d.chunks_used || 0}`,
                ].join("\n");
                await showMarkdown(content, "answer");
            } catch (e: any) {
                vscode.window.showErrorMessage(`Memcon: ${e.message}`);
            }
        }
    );
}

async function search(): Promise<void> {
    const q = await vscode.window.showInputBox({
        prompt: "Memcon search (raw chunks)",
        placeHolder: "imu calibration backward gait",
        ignoreFocusOut: true,
    });
    if (!q || !q.trim()) return;

    try {
        const d = await memconFetch("/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: q, top_k: Math.max(5, getTopK()) }),
        });
        const chunks = d.results || [];
        if (!chunks.length) {
            vscode.window.showInformationMessage("Memcon: no results");
            return;
        }
        const content = [
            `# Search: ${q}`,
            "",
            ...chunks.map((c: any) =>
                [
                    `## ${c.score}  ·  ${c.doc_name}`,
                    `*${c.subsystem} / ${c.memory_type}*`,
                    "",
                    "```",
                    c.text,
                    "```",
                    "",
                ].join("\n")
            ),
        ].join("\n");
        await showMarkdown(content, `${chunks.length} chunks`);
    } catch (e: any) {
        vscode.window.showErrorMessage(`Memcon: ${e.message}`);
    }
}

async function saveSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage("Memcon: no active editor");
        return;
    }
    const selected = editor.document.getText(editor.selection);
    if (!selected.trim()) {
        vscode.window.showWarningMessage(
            "Memcon: nothing selected. Highlight some text first."
        );
        return;
    }

    const relPath = vscode.workspace.asRelativePath(editor.document.fileName);
    const note = await vscode.window.showInputBox({
        prompt: "Add a note about this snippet (optional)",
        placeHolder: "Why am I saving this?",
        ignoreFocusOut: true,
    });

    const summary = [
        `Captured from \`${relPath}\``,
        note ? `\n${note}\n` : "",
        "```",
        selected,
        "```",
    ].join("\n");

    try {
        const d = await memconFetch("/memory/session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ summary, subsystem: "unknown" }),
        });
        vscode.window.showInformationMessage(`Memcon: saved → ${d.path}`);
        vscode.commands.executeCommand("memcon.refreshRecent");
    } catch (e: any) {
        vscode.window.showErrorMessage(`Memcon: ${e.message}`);
    }
}

async function openDashboard(): Promise<void> {
    await vscode.env.openExternal(vscode.Uri.parse(`${getApiUrl()}/ui`));
}

async function openNote(path: string): Promise<void> {
    try {
        const d = await memconFetch(
            `/memory/note?path=${encodeURIComponent(path)}`
        );
        const doc = await vscode.workspace.openTextDocument({
            language: "markdown",
            content: d.content,
        });
        await vscode.window.showTextDocument(doc, { preview: true });
    } catch (e: any) {
        vscode.window.showErrorMessage(`Memcon: ${e.message}`);
    }
}

// ── Sidebar — Recent activity tree ───────────────────────────────────────

interface Note {
    path: string;
    name: string;
    folder: string;
    mtime: number;
    size: number;
}

class RecentProvider implements vscode.TreeDataProvider<RecentItem> {
    private readonly _onDidChangeTreeData = new vscode.EventEmitter<
        RecentItem | undefined
    >();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
    private _inFlight = false;

    get inFlight(): boolean {
        return this._inFlight;
    }

    refresh(): void {
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(item: RecentItem): vscode.TreeItem {
        return item;
    }

    async getChildren(): Promise<RecentItem[]> {
        this._inFlight = true;
        try {
            const d = await memconFetch(
                `/memory/recent?limit=${getRecentLimit()}`
            );
            const notes: Note[] = d.notes || [];
            if (!notes.length) {
                return [RecentItem.placeholder("(vault is empty)")];
            }
            return notes.map((n) => new RecentItem(n));
        } catch (e: any) {
            return [
                RecentItem.placeholder(`(api offline — ${getApiUrl()})`),
            ];
        } finally {
            this._inFlight = false;
        }
    }
}

class RecentItem extends vscode.TreeItem {
    constructor(note: Note | { name: string }) {
        super(note.name, vscode.TreeItemCollapsibleState.None);
        if ("path" in note && note.path) {
            this.description = `${note.folder} · ${timeAgo(note.mtime)}`;
            this.tooltip = note.path;
            this.iconPath = new vscode.ThemeIcon("note");
            this.command = {
                command: "memcon.openNote",
                title: "Open in editor",
                arguments: [note.path],
            };
        } else {
            this.iconPath = new vscode.ThemeIcon("info");
            this.description = "";
        }
    }

    static placeholder(text: string): RecentItem {
        return new RecentItem({ name: text });
    }
}

// ── Activation ───────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext): void {
    const recent = new RecentProvider();

    context.subscriptions.push(
        vscode.commands.registerCommand("memcon.ask", ask),
        vscode.commands.registerCommand("memcon.search", search),
        vscode.commands.registerCommand("memcon.saveSelection", saveSelection),
        vscode.commands.registerCommand("memcon.openDashboard", openDashboard),
        vscode.commands.registerCommand("memcon.openNote", openNote),
        vscode.commands.registerCommand("memcon.refreshRecent", () =>
            recent.refresh()
        ),
        vscode.window.registerTreeDataProvider("memconRecent", recent)
    );

    // Refresh the sidebar every couple of minutes so it doesn't go stale. Skip a
    // tick if a previous refresh is still in flight, so a slow API can't stack up
    // overlapping requests (the timeout in memconFetch bounds each one).
    const tick = setInterval(() => {
        if (!recent.inFlight) recent.refresh();
    }, 120_000);
    context.subscriptions.push({ dispose: () => clearInterval(tick) });

    // Friendly first-launch hint. Persist "seen" UNCONDITIONALLY up front so the
    // toast can't reappear every launch if the user dismisses it without clicking.
    const seen = context.globalState.get<boolean>("memcon.seenWelcome", false);
    if (!seen) {
        context.globalState.update("memcon.seenWelcome", true);
        vscode.window
            .showInformationMessage(
                "Memcon ready. Press Cmd+Shift+M (Ctrl+Shift+M on Linux/Windows) to ask.",
                "Open dashboard",
                "Got it"
            )
            .then((choice) => {
                if (choice === "Open dashboard") openDashboard();
            });
    }
}

export function deactivate(): void {
    // nothing to do
}
