using LibraryApi.Models;

namespace LibraryApi.Services
{
    public interface IBookService
    {
        List<Book> GetBooks();
        Book? GetBook(int id);
        void AddBook(Book book);
        bool UpdateBook(Book book);
        bool DeleteBook(int id);
    }
}