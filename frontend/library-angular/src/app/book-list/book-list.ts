import {
  ChangeDetectorRef,
  Component,
  OnInit
} from '@angular/core';

import { Book } from '../book';
import { BookService } from '../services/book';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-book-list',
  standalone: true,
  templateUrl: './book-list.html',
  styleUrl: './book-list.css'
})
export class BookList implements OnInit {
  books: Book[] = [];
  loading = false;
  errorMessage = '';

  constructor(
    private bookService: BookService,
    public authService: AuthService,
    private changeDetector: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadBooks();
  }

  loadBooks(): void {
    this.loading = true;
    this.errorMessage = '';

    this.bookService.getBooks().subscribe({
      next: (data) => {
        this.books = data;
        this.loading = false;

        this.changeDetector.detectChanges();
      },

      error: (error) => {
        console.error(error);

        this.errorMessage =
          'Could not load books.';

        this.loading = false;

        this.changeDetector.detectChanges();
      }
    });
  }

  deleteBook(id: number): void {
    this.bookService.deleteBook(id).subscribe({
      next: () => {
        this.loadBooks();
      },

      error: (error) => {
        console.error(error);

        if (error.status === 403) {
          this.errorMessage =
            'Only Admin users can delete books.';
        } else if (error.status === 401) {
          this.errorMessage =
            'Please log in first.';
        } else {
          this.errorMessage =
            'Could not delete book.';
        }

        this.changeDetector.detectChanges();
      }
    });
  }
}