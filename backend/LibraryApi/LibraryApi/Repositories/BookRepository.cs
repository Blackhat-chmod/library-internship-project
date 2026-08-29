using LibraryApi.Data;
using LibraryApi.Models;
using Microsoft.EntityFrameworkCore;

namespace LibraryApi.Repositories
{
    public class BookRepository : IBookRepository
    {
        private readonly LibraryDbContext context;

        public BookRepository(LibraryDbContext context)
        {
            this.context = context;
        }

        public async Task<List<Book>> GetAllAsync()
        {
            return await context.Books
                .Include(book => book.AuthorEntity)
                .Include(book => book.Categories)
                .ToListAsync();
        }

        public async Task<Book?> GetByIdAsync(int id)
        {
            return await context.Books
                .Include(book => book.AuthorEntity)
                .Include(book => book.Categories)
                .FirstOrDefaultAsync(book => book.BookId == id);
        }

        public async Task<Book> AddAsync(Book book)
        {
            context.Books.Add(book);
            await context.SaveChangesAsync();

            return book;
        }

        public async Task<bool> UpdateAsync(Book book)
        {
            Book? existingBook = await context.Books
                .FirstOrDefaultAsync(b => b.BookId == book.BookId);

            if (existingBook == null)
            {
                return false;
            }

            existingBook.Title = book.Title;
            existingBook.AuthorId = book.AuthorId;

            await context.SaveChangesAsync();

            return true;
        }

        public async Task<bool> DeleteAsync(int id)
        {
            Book? book = await context.Books
                .FirstOrDefaultAsync(b => b.BookId == id);

            if (book == null)
            {
                return false;
            }

            context.Books.Remove(book);
            await context.SaveChangesAsync();

            return true;
        }
    }
}