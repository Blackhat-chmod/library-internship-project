using LibraryApi.Models;
using Microsoft.EntityFrameworkCore;

namespace LibraryApi.Data
{
    public class LibraryDbContext : DbContext
    {
        public LibraryDbContext(
            DbContextOptions<LibraryDbContext> options)
            : base(options)
        {
        }

        public DbSet<Book> Books => Set<Book>();

        public DbSet<Author> Authors => Set<Author>();

        public DbSet<Category> Categories => Set<Category>();

        public DbSet<User> Users => Set<User>();

        public DbSet<Reservation> Reservations
            => Set<Reservation>();

        public DbSet<AgentThread> AgentThreads
            => Set<AgentThread>();

        protected override void OnModelCreating(
            ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Book>()
                .HasOne(book => book.AuthorEntity)
                .WithMany(author => author.Books)
                .HasForeignKey(book => book.AuthorId);

            modelBuilder.Entity<Book>()
                .HasMany(book => book.Categories)
                .WithMany(category => category.Books);

            modelBuilder.Entity<Reservation>()
                .HasOne(reservation => reservation.Book)
                .WithMany()
                .HasForeignKey(reservation => reservation.BookId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<Reservation>()
                .HasOne(reservation => reservation.User)
                .WithMany()
                .HasForeignKey(reservation => reservation.UserId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<Reservation>()
                .HasIndex(reservation => new
                {
                    reservation.UserId,
                    reservation.IdempotencyKey
                })
                .IsUnique();

            modelBuilder.Entity<Reservation>()
                .HasIndex(reservation => new
                {
                    reservation.BookId,
                    reservation.UserId
                })
                .IsUnique();

            modelBuilder.Entity<AgentThread>()
                .HasOne(thread => thread.User)
                .WithMany()
                .HasForeignKey(thread => thread.UserId)
                .OnDelete(DeleteBehavior.Cascade);
        }
    }
}