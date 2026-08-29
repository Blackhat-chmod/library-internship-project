using LibraryApi.Models;

namespace LibraryApi.Repositories
{
    public class BookRepository : IBookRepository
    {
        private readonly List<Book> books = new()
        {
            new Book
            {
                Id = 1,
                Title = "C# Basics",
                Author = "John Smith",
                Category = "Programming"
            },
            new Book
            {
                Id = 2,
                Title = "Angular Essentials",
                Author = "Sarah Khan",
                Category = "Web Development"
            }
        };

        public List<Book> GetAll()
        {
            return books;
        }

        public Book? GetById(int id)
        {
            return books.FirstOrDefault(b => b.Id == id);
        }

        public void Add(Book book)
        {
            book.Id = books.Count == 0
                ? 1
                : books.Max(b => b.Id) + 1;

            books.Add(book);
        }

        public bool Update(Book book)
        {
            Book? existingBook = GetById(book.Id);

            if (existingBook == null)
            {
                return false;
            }

            existingBook.Title = book.Title;
            existingBook.Author = book.Author;
            existingBook.Category = book.Category;

            return true;
        }

        public bool Delete(int id)
        {
            Book? book = GetById(id);

            if (book == null)
            {
                return false;
            }

            books.Remove(book);
            return true;
        }
    }
}