import { Component } from '@angular/core';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { BookService } from '../services/book';

@Component({
  selector: 'app-book-form',
  imports: [ReactiveFormsModule],
  templateUrl: './book-form.html',
  styleUrl: './book-form.css'
})
export class BookForm {

  bookForm = new FormGroup({
    title: new FormControl('', Validators.required),
    author: new FormControl('', Validators.required),
    category: new FormControl('', Validators.required)
  });

  constructor(private bookService: BookService) {}

  addBook() {
    if (this.bookForm.valid) {
      this.bookService.addBook({
        id: 0,
        title: this.bookForm.value.title ?? '',
        author: this.bookForm.value.author ?? '',
        category: this.bookForm.value.category ?? ''
      });

      alert('Book added successfully');

      this.bookForm.reset();
    }
  }
}