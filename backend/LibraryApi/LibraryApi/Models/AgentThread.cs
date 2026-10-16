using System.ComponentModel.DataAnnotations;

namespace LibraryApi.Models
{
    public class AgentThread
    {
        [Key]
        [MaxLength(100)]
        public string ThreadId { get; set; }
            = string.Empty;

        public int UserId { get; set; }

        public DateTime CreatedAt { get; set; }
            = DateTime.UtcNow;

        public User? User { get; set; }
    }
}