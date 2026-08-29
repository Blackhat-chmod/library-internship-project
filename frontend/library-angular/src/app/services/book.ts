import { Injectable } from '@angular/core';
import { Book } from '../book';

@Injectable({
  providedIn: 'root'
})
export class BookService {

  private books: Book[] = [
    {
      id: 1,
      title: 'C# Basics',
      author: 'John Smith',
      category: 'Programming'
    },
    {
      id: 2,
      title: 'Angular Essentials',
      author: 'Sarah Khan',
      category: 'Web Development'
    }
  ];

  getBooks(): Book[] {
    return this.books;
  }

  addBook(book: Book) {
    book.id = this.books.length + 1;
    this.books.push(book);
  }
}