import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { Book } from '../book';
import { BookService } from '../services/book';

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
        this.errorMessage = 'Could not load books.';
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
        this.errorMessage = 'Could not delete book.';
        this.changeDetector.detectChanges();
      }
    });
  }
}