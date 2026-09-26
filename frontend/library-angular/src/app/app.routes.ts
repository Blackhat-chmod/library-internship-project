import { Routes } from '@angular/router';
import { BookList } from './book-list/book-list';
import { BookForm } from './book-form/book-form';
import { Login } from './login/login';
import { AssistantChat } from './assistant-chat/assistant-chat';
import { authGuard } from './services/auth.guard';

export const routes: Routes = [
  {
    path: '',
    component: BookList
  },

  {
    path: 'login',
    component: Login
  },

  {
    path: 'add-book',
    component: BookForm,
    canActivate: [authGuard]
  },

  {
    path: 'assistant',
    component: AssistantChat,
    canActivate: [authGuard]
  },

  {
    path: '**',
    redirectTo: ''
  }
];