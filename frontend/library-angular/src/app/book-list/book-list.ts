import { Component } from '@angular/core';
import { Book } from '../book';
import { BookService } from '../services/book';

@Component({
  selector: 'app-book-list',
  imports: [],
  templateUrl: './book-list.html',
  styleUrl: './book-list.css'
})
export class BookList {

  books: Book[];

  constructor(private bookService: BookService) {
    this.books = this.bookService.getBooks();
  }
}