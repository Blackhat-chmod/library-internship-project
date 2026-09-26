import {
  ChangeDetectorRef,
  Component
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../services/auth.service';

interface StreamEvent {
  type: 'token' | 'sources' | 'done' | 'error';
  content?: string;
  sources?: string[];
  completed?: boolean;
  message?: string;
}

@Component({
  selector: 'app-assistant-chat',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './assistant-chat.html',
  styleUrl: './assistant-chat.css'
})
export class AssistantChat {
  question = '';
  answer = '';
  sources: string[] = [];
  errorMessage = '';
  isStreaming = false;

  private abortController: AbortController | null = null;

  constructor(
    private authService: AuthService,
    private changeDetector: ChangeDetectorRef
  ) {}

  async ask(): Promise<void> {
    const trimmedQuestion = this.question.trim();

    if (!trimmedQuestion) {
      this.errorMessage = 'Please enter a question.';
      return;
    }

    const token = this.authService.getToken();

    if (!token) {
      this.errorMessage = 'Please login first.';
      return;
    }

    this.answer = '';
    this.sources = [];
    this.errorMessage = '';
    this.isStreaming = true;

    this.changeDetector.detectChanges();

    this.abortController = new AbortController();

    try {
      const response = await fetch(
        'https://localhost:7272/api/assistant/ask/stream',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            question: trimmedQuestion,
            delayMs: 150
          }),
          signal: this.abortController.signal
        }
      );

      if (!response.ok) {
        throw new Error(
          `Request failed with status ${response.status}`
        );
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

        const events = buffer.split('\n\n');

        buffer = events.pop() ?? '';

        for (const eventBlock of events) {
          const lines = eventBlock.split('\n');

          for (const line of lines) {
            if (!line.startsWith('data:')) {
              continue;
            }

            const jsonText = line
              .substring(5)
              .trim();

            if (!jsonText) {
              continue;
            }

            const event: StreamEvent =
              JSON.parse(jsonText);

            this.handleStreamEvent(event);

            this.changeDetector.detectChanges();
          }
        }
      }
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        this.errorMessage =
          'Streaming was cancelled.';
      } else {
        this.errorMessage =
          error?.message ||
          'Could not connect to the AI assistant.';
      }

      this.changeDetector.detectChanges();
    } finally {
      this.isStreaming = false;
      this.abortController = null;

      this.changeDetector.detectChanges();
    }
  }

  stop(): void {
    if (this.abortController) {
      this.abortController.abort();
    }
  }

  clear(): void {
    if (this.isStreaming) {
      this.stop();
    }

    this.question = '';
    this.answer = '';
    this.sources = [];
    this.errorMessage = '';

    this.changeDetector.detectChanges();
  }

  private handleStreamEvent(
    event: StreamEvent
  ): void {
    if (
      event.type === 'token' &&
      event.content
    ) {
      this.answer += event.content;
      return;
    }

    if (
      event.type === 'sources' &&
      event.sources
    ) {
      this.sources = event.sources;
      return;
    }

    if (
      event.type === 'error' &&
      event.message
    ) {
      this.errorMessage = event.message;
      return;
    }

    if (event.type === 'done') {
      this.isStreaming = false;
    }
  }
}