import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Book } from '../book';

@Injectable({
  providedIn: 'root'
})
export class BookService {
  private readonly apiUrl =
    'https://localhost:7272/api/Books';

  constructor(private http: HttpClient) {}

  getBooks(): Observable<Book[]> {
    return this.http.get<Book[]>(this.apiUrl);
  }

  getBookById(id: number): Observable<Book> {
    return this.http.get<Book>(
      `${this.apiUrl}/${id}`
    );
  }

  addBook(book: Book): Observable<Book> {
    return this.http.post<Book>(
      this.apiUrl,
      book
    );
  }

  updateBook(
    id: number,
    book: Book
  ): Observable<unknown> {
    return this.http.put(
      `${this.apiUrl}/${id}`,
      book
    );
  }

  deleteBook(id: number): Observable<unknown> {
    return this.http.delete(
      `${this.apiUrl}/${id}`
    );
  }
}