using LibraryApi.Models;

namespace LibraryApi.Repositories
{
    public interface IBookRepository
    {
        List<Book> GetAll();
        Book? GetById(int id);
        void Add(Book book);
        bool Update(Book book);
        bool Delete(int id);
    }
}