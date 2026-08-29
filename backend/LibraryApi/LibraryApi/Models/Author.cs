namespace LibraryApi.Models
{
    public class Author
    {
        public int AuthorId { get; set; }

        public string FullName { get; set; } = string.Empty;

        public List<Book> Books { get; set; } = new List<Book>();
    }
}