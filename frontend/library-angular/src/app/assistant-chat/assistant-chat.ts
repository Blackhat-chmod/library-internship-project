import {
  ChangeDetectorRef,
  Component,
  OnInit
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../services/auth.service';

interface AgentToolCall {
  name: string;
  args: Record<string, unknown>;
}

interface TimelineItem {
  kind:
    | 'started'
    | 'tool_call'
    | 'tool_result'
    | 'approval'
    | 'final'
    | 'error'
    | 'cancelled';
  title: string;
  detail: string;
}

interface RunStatus {
  threadId?: string;
  status?: string;
  pendingApproval?: unknown;
  approvalRequired?: unknown;
  answer?: string;
  [key: string]: unknown;
}

@Component({
  selector: 'app-assistant-chat',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './assistant-chat.html',
  styleUrl: './assistant-chat.css'
})
export class AssistantChat implements OnInit {
  question = '';
  answer = '';
  sources: string[] = [];
  errorMessage = '';

  threadId = '';

  isStreaming = false;
  isResuming = false;
  isCancelling = false;

  pendingApproval = false;
  approvalCalls: AgentToolCall[] = [];

  timeline: TimelineItem[] = [];

  private abortController: AbortController | null = null;

  private readonly apiBaseUrl =
    'http://localhost:5087/api/assistant/agent/runs';

  private readonly storageKey =
    'week7-agent-thread-id';

  constructor(
    private authService: AuthService,
    private changeDetector: ChangeDetectorRef
  ) {}

  async ngOnInit(): Promise<void> {
    const storedThreadId =
      localStorage.getItem(this.storageKey);

    if (!storedThreadId) {
      return;
    }

    this.threadId = storedThreadId;

    await this.restoreRun();
  }

  async ask(): Promise<void> {
    const trimmedQuestion = this.question.trim();

    if (!trimmedQuestion) {
      this.errorMessage = 'Please enter a message.';
      return;
    }

    const token = this.authService.getToken();

    if (!token) {
      this.errorMessage = 'Please login first.';
      return;
    }

    this.resetRunDisplay();

    this.isStreaming = true;
    this.errorMessage = '';

    this.addTimeline(
      'started',
      'Agent run started',
      trimmedQuestion
    );

    this.abortController = new AbortController();

    this.changeDetector.detectChanges();

    try {
      const response = await fetch(
        this.apiBaseUrl,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            message: trimmedQuestion
          }),
          signal: this.abortController.signal
        }
      );

      await this.consumeResponse(response);
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        if (!this.isCancelling) {
          this.errorMessage =
            'The agent request was stopped.';
        }
      } else {
        this.handleRequestFailure(error);
      }
    } finally {
      this.isStreaming = false;
      this.abortController = null;

      this.changeDetector.detectChanges();
    }
  }

  async approve(): Promise<void> {
    await this.resumeRun(true);
  }

  async reject(): Promise<void> {
    await this.resumeRun(false);
  }

  async cancel(): Promise<void> {
    if (!this.threadId || this.isCancelling) {
      return;
    }

    const token = this.authService.getToken();

    if (!token) {
      this.errorMessage = 'Please login first.';
      return;
    }

    this.isCancelling = true;
    this.errorMessage = '';

    this.changeDetector.detectChanges();

    try {
      const response = await fetch(
        `${this.apiBaseUrl}/${encodeURIComponent(
          this.threadId
        )}/cancel`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw await this.createHttpError(response);
      }

      this.abortController?.abort();

      this.isStreaming = false;
      this.isResuming = false;
      this.pendingApproval = false;
      this.approvalCalls = [];

      this.addTimeline(
        'cancelled',
        'Run cancelled',
        'The agent run was cancelled.'
      );
    } catch (error: any) {
      this.handleRequestFailure(error);
    } finally {
      this.isCancelling = false;

      this.changeDetector.detectChanges();
    }
  }

  clear(): void {
    if (this.isStreaming || this.isResuming) {
      this.abortController?.abort();
    }

    this.question = '';
    this.answer = '';
    this.sources = [];
    this.errorMessage = '';
    this.threadId = '';

    this.isStreaming = false;
    this.isResuming = false;
    this.isCancelling = false;

    this.pendingApproval = false;
    this.approvalCalls = [];

    this.timeline = [];

    this.abortController = null;

    localStorage.removeItem(this.storageKey);

    this.changeDetector.detectChanges();
  }

  formatArguments(
    args: Record<string, unknown>
  ): string {
    try {
      return JSON.stringify(args, null, 2);
    } catch {
      return String(args);
    }
  }

  private async resumeRun(
    approved: boolean
  ): Promise<void> {
    if (
      !this.threadId ||
      !this.pendingApproval ||
      this.isResuming
    ) {
      return;
    }

    const token = this.authService.getToken();

    if (!token) {
      this.errorMessage = 'Please login first.';
      return;
    }

    this.isResuming = true;
    this.pendingApproval = false;
    this.errorMessage = '';

    this.addTimeline(
      'approval',
      approved
        ? 'Action approved'
        : 'Action rejected',
      approved
        ? 'You approved the pending write action.'
        : 'You rejected the pending write action.'
    );

    this.abortController = new AbortController();

    this.changeDetector.detectChanges();

    try {
      const response = await fetch(
        `${this.apiBaseUrl}/${encodeURIComponent(
          this.threadId
        )}/resume`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            approved
          }),
          signal: this.abortController.signal
        }
      );

      await this.consumeResponse(response);
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        if (!this.isCancelling) {
          this.errorMessage =
            'The resumed agent request was stopped.';
        }
      } else {
        this.handleRequestFailure(error);
      }
    } finally {
      this.isResuming = false;
      this.abortController = null;

      this.changeDetector.detectChanges();
    }
  }

  private async restoreRun(): Promise<void> {
    const token = this.authService.getToken();

    if (!token || !this.threadId) {
      return;
    }

    try {
      const response = await fetch(
        `${this.apiBaseUrl}/${encodeURIComponent(
          this.threadId
        )}`,
        {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (response.status === 404) {
        localStorage.removeItem(this.storageKey);
        this.threadId = '';
        return;
      }

      if (!response.ok) {
        throw await this.createHttpError(response);
      }

      const status =
        await response.json() as RunStatus;

      this.applyRestoredStatus(status);
    } catch (error: any) {
      this.handleRequestFailure(error);
    } finally {
      this.changeDetector.detectChanges();
    }
  }

  private applyRestoredStatus(
    status: RunStatus
  ): void {
    const statusText =
      typeof status.status === 'string'
        ? status.status
        : 'saved';

    this.addTimeline(
      'started',
      'Previous agent thread restored',
      `Status: ${statusText}`
    );

    const pending =
      status.pendingApproval ??
      status.approvalRequired;

    if (pending) {
      this.pendingApproval = true;

      this.approvalCalls =
        this.extractApprovalCalls(pending);

      this.addTimeline(
        'approval',
        'Approval still required',
        'This action was restored after page refresh.'
      );
    }

    if (
      typeof status.answer === 'string' &&
      status.answer
    ) {
      this.answer = status.answer;
    }
  }

  private extractApprovalCalls(
    value: unknown
  ): AgentToolCall[] {
    if (Array.isArray(value)) {
      return value
        .filter(
          item =>
            typeof item === 'object' &&
            item !== null
        )
        .map(item => {
          const record =
            item as Record<string, unknown>;

          return {
            name:
              typeof record['name'] === 'string'
                ? record['name']
                : 'write_action',
            args:
              this.toRecord(record['args'])
          };
        });
    }

    if (
      typeof value === 'object' &&
      value !== null
    ) {
      const record =
        value as Record<string, unknown>;

      if (Array.isArray(record['calls'])) {
        return this.extractApprovalCalls(
          record['calls']
        );
      }

      return [
        {
          name:
            typeof record['name'] === 'string'
              ? record['name']
              : typeof record['tool_name'] === 'string'
                ? record['tool_name']
                : 'write_action',
          args: this.toRecord(
            record['args'] ??
            record['arguments']
          )
        }
      ];
    }

    return [];
  }

  private toRecord(
    value: unknown
  ): Record<string, unknown> {
    if (
      typeof value === 'object' &&
      value !== null &&
      !Array.isArray(value)
    ) {
      return value as Record<string, unknown>;
    }

    return {};
  }

  private async consumeResponse(
    response: Response
  ): Promise<void> {
    if (!response.ok) {
      throw await this.createHttpError(response);
    }

    if (!response.body) {
      throw new Error(
        'Streaming response body is unavailable.'
      );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = '';

    while (true) {
      const result = await reader.read();

      if (result.done) {
        break;
      }

      buffer += decoder.decode(
        result.value,
        {
          stream: true
        }
      );

      buffer = this.consumeSseBuffer(
        buffer,
        false
      );

      this.changeDetector.detectChanges();
    }

    buffer += decoder.decode();

    this.consumeSseBuffer(
      buffer,
      true
    );

    this.changeDetector.detectChanges();
  }

  private consumeSseBuffer(
    buffer: string,
    flush: boolean
  ): string {
    const normalized =
      buffer.replace(/\r\n/g, '\n');

    const blocks =
      normalized.split('\n\n');

    let remainder = '';

    if (!flush) {
      remainder = blocks.pop() ?? '';
    }

    for (const block of blocks) {
      if (!block.trim()) {
        continue;
      }

      this.handleSseBlock(block);
    }

    if (flush && remainder.trim()) {
      this.handleSseBlock(remainder);
      return '';
    }

    return remainder;
  }

  private handleSseBlock(
    block: string
  ): void {
    const lines = block.split('\n');

    let eventName = 'message';
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventName =
          line.substring(6).trim();
        continue;
      }

      if (line.startsWith('data:')) {
        dataLines.push(
          line.substring(5).trimStart()
        );
      }
    }

    if (dataLines.length === 0) {
      return;
    }

    const jsonText =
      dataLines.join('\n');

    let payload: Record<string, any>;

    try {
      payload = JSON.parse(jsonText);
    } catch {
      this.errorMessage =
        'The agent returned an invalid stream event.';

      this.addTimeline(
        'error',
        'Invalid stream event',
        jsonText
      );

      return;
    }

    this.handleAgentEvent(
      eventName,
      payload
    );
  }

  private handleAgentEvent(
    eventName: string,
    payload: Record<string, any>
  ): void {
    switch (eventName) {
      case 'thread': {
        const receivedThreadId =
          typeof payload['threadId'] === 'string'
            ? payload['threadId']
            : '';

        if (receivedThreadId) {
          this.threadId = receivedThreadId;

          localStorage.setItem(
            this.storageKey,
            receivedThreadId
          );
        }

        return;
      }

      case 'step': {
        const kind =
          payload['kind'] === 'tool_result'
            ? 'tool_result'
            : 'tool_call';

        const name =
          typeof payload['name'] === 'string'
            ? payload['name']
            : 'agent';

        const summary =
          typeof payload['summary'] === 'string'
            ? payload['summary']
            : '';

        this.addTimeline(
          kind,
          kind === 'tool_result'
            ? `Tool result: ${name}`
            : `Tool call: ${name}`,
          summary
        );

        return;
      }

      case 'approval_required': {
        this.pendingApproval = true;

        this.approvalCalls =
          this.extractApprovalCalls(
            payload['calls']
          );

        this.addTimeline(
          'approval',
          'Approval required',
          'A write action is waiting for your decision.'
        );

        return;
      }

      case 'token': {
        const text =
          typeof payload['text'] === 'string'
            ? payload['text']
            : '';

        this.answer += text;

        return;
      }

      case 'final': {
        const finalAnswer =
          typeof payload['answer'] === 'string'
            ? payload['answer']
            : '';

        if (
          finalAnswer &&
          !this.answer
        ) {
          this.answer = finalAnswer;
        }

        this.sources =
          Array.isArray(payload['sources'])
            ? payload['sources']
                .filter(
                  (source: unknown) =>
                    typeof source === 'string'
                )
            : [];

        this.pendingApproval = false;
        this.approvalCalls = [];

        this.addTimeline(
          'final',
          'Run completed',
          finalAnswer ||
            'The agent run completed.'
        );

        return;
      }

      case 'error': {
        const code =
          typeof payload['code'] === 'string'
            ? payload['code']
            : 'agent_error';

        const message =
          typeof payload['message'] === 'string'
            ? payload['message']
            : 'The agent run failed.';

        this.errorMessage = message;

        this.addTimeline(
          'error',
          `Agent error: ${code}`,
          message
        );

        return;
      }
    }
  }

  private resetRunDisplay(): void {
    this.answer = '';
    this.sources = [];
    this.errorMessage = '';
    this.threadId = '';

    this.pendingApproval = false;
    this.approvalCalls = [];

    this.timeline = [];

    localStorage.removeItem(this.storageKey);
  }

  private addTimeline(
    kind: TimelineItem['kind'],
    title: string,
    detail: string
  ): void {
    this.timeline.push({
      kind,
      title,
      detail
    });
  }

  private handleRequestFailure(
    error: any
  ): void {
    const message =
      error?.message ||
      'Could not connect to the AI agent.';

    this.errorMessage = message;

    this.addTimeline(
      'error',
      'Request failed',
      message
    );
  }

  private async createHttpError(
    response: Response
  ): Promise<Error> {
    let message =
      `Request failed with status ${response.status}.`;

    try {
      const body = await response.json();

      if (
        body &&
        typeof body.message === 'string'
      ) {
        message = body.message;
      }
    } catch {
      // Keep the status-based fallback message.
    }

    if (response.status === 429) {
      message =
        'Too many assistant requests. Please wait and try again.';
    } else if (response.status === 404) {
      message =
        'This agent thread was not found or does not belong to you.';
    } else if (
      response.status === 502 ||
      response.status === 503
    ) {
      message =
        'The AI agent service is temporarily unavailable.';
    }

    return new Error(message);
  }
}