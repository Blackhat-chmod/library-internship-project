using System.ComponentModel.DataAnnotations;

namespace LibraryApi.Models
{
    public class Reservation
    {
        public int Id { get; set; }

        public int BookId { get; set; }

        public int UserId { get; set; }

        public DateTime CreatedAt { get; set; }
            = DateTime.UtcNow;

        [Required]
        [MaxLength(100)]
        public string IdempotencyKey { get; set; }
            = string.Empty;

        public Book? Book { get; set; }

        public User? User { get; set; }
    }
}