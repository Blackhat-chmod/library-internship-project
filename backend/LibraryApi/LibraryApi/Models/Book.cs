using System.ComponentModel.DataAnnotations.Schema;

namespace LibraryApi.Models
{
    public class Book
    {
        public int BookId { get; set; }

        [NotMapped]
        public int Id
        {
            get => BookId;
            set => BookId = value;
        }

        public string Title { get; set; } = string.Empty;

        public int AuthorId { get; set; }

        public Author? AuthorEntity { get; set; }

        [NotMapped]
        public string Author { get; set; } = string.Empty;

        [NotMapped]
        public string Category { get; set; } = string.Empty;

        public bool IsAvailable { get; set; } = true;

        public List<Category> Categories { get; set; } = new List<Category>();
    }
}