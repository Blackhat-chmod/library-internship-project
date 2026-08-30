export interface Author {
  authorId: number;
  fullName: string;
}

export interface Category {
  categoryId: number;
  categoryName: string;
}

export interface Book {
  bookId: number;
  id?: number;
  title: string;
  authorId: number;
  authorEntity?: Author | null;
  author?: string;
  category?: string;
  categories: Category[];
}