using LibraryApi.Models;
using Microsoft.EntityFrameworkCore;

namespace LibraryApi.Data
{
    public class LibraryDbContext : DbContext
    {
        public LibraryDbContext(DbContextOptions<LibraryDbContext> options)
            : base(options)
        {
        }

        public DbSet<Book> Books => Set<Book>();
        public DbSet<Author> Authors => Set<Author>();
        public DbSet<Category> Categories => Set<Category>();

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Book>()
                .HasOne(book => book.AuthorEntity)
                .WithMany(author => author.Books)
                .HasForeignKey(book => book.AuthorId);

            modelBuilder.Entity<Book>()
                .HasMany(book => book.Categories)
                .WithMany(category => category.Books);
        }
    }
}