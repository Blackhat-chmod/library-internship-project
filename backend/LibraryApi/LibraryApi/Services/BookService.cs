using LibraryApi.Models;
using LibraryApi.Repositories;

namespace LibraryApi.Services
{
    public class BookService : IBookService
    {
        private readonly IBookRepository bookRepository;

        public BookService(IBookRepository bookRepository)
        {
            this.bookRepository = bookRepository;
        }

        public async Task<List<Book>> GetAllBooksAsync()
        {
            return await bookRepository.GetAllAsync();
        }

        public async Task<Book?> GetBookByIdAsync(int id)
        {
            return await bookRepository.GetByIdAsync(id);
        }

        public async Task<Book> AddBookAsync(Book book)
        {
            return await bookRepository.AddAsync(book);
        }

        public async Task<bool> UpdateBookAsync(Book book)
        {
            return await bookRepository.UpdateAsync(book);
        }

        public async Task<bool> DeleteBookAsync(int id)
        {
            return await bookRepository.DeleteAsync(id);
        }
    }
}