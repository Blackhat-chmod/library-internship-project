using LibraryApi.Models;
using LibraryApi.Repositories;

namespace LibraryApi.Services
{
    public class BookService : IBookService
    {
        private readonly IBookRepository repository;

        public BookService(IBookRepository repository)
        {
            this.repository = repository;
        }

        public List<Book> GetBooks()
        {
            return repository.GetAll();
        }

        public Book? GetBook(int id)
        {
            return repository.GetById(id);
        }

        public void AddBook(Book book)
        {
            repository.Add(book);
        }

        public bool UpdateBook(Book book)
        {
            return repository.Update(book);
        }

        public bool DeleteBook(int id)
        {
            return repository.Delete(id);
        }
    }
}