import { Routes } from '@angular/router';
import { BookList } from './book-list/book-list';
import { BookForm } from './book-form/book-form';

export const routes: Routes = [
  {
    path: '',
    component: BookList
  },
  {
    path: 'add-book',
    component: BookForm
  }
];