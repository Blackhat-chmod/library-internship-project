import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { BookService } from '../services/book';

@Component({
  selector: 'app-book-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './book-form.html',
  styleUrl: './book-form.css'
})
export class BookForm {

  bookForm: FormGroup;
  errorMessage = '';

  constructor(
    private formBuilder: FormBuilder,
    private bookService: BookService,
    private router: Router
  ) {
    this.bookForm = this.formBuilder.group({
      title: ['', Validators.required],
      authorId: [3, Validators.required]
    });
  }

  submitForm(): void {
    if (this.bookForm.invalid) {
      this.bookForm.markAllAsTouched();
      return;
    }

    const book = {
      bookId: 0,
      title: this.bookForm.value.title,
      authorId: Number(this.bookForm.value.authorId),
      authorEntity: null,
      author: '',
      category: '',
      categories: []
    };

    this.bookService.addBook(book).subscribe({
      next: () => {
        this.router.navigate(['/']);
      },

      error: () => {
        this.errorMessage = 'Could not add book.';
      }
    });
  }
}