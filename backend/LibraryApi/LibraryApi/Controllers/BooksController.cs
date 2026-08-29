using LibraryApi.Models;
using LibraryApi.Services;
using Microsoft.AspNetCore.Mvc;

namespace LibraryApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class BooksController : ControllerBase
    {
        private readonly IBookService service;

        public BooksController(IBookService service)
        {
            this.service = service;
        }

        [HttpGet]
        public IActionResult GetAllBooks()
        {
            return Ok(service.GetBooks());
        }

        [HttpGet("{id}")]
        public IActionResult GetBookById(int id)
        {
            Book? book = service.GetBook(id);

            if (book == null)
            {
                return NotFound("Book not found.");
            }

            return Ok(book);
        }

        [HttpPost]
        public IActionResult AddBook(Book book)
        {
            if (string.IsNullOrWhiteSpace(book.Title))
            {
                return BadRequest("Book title is required.");
            }

            service.AddBook(book);

            return CreatedAtAction(
                nameof(GetBookById),
                new { id = book.Id },
                book
            );
        }

        [HttpPut("{id}")]
        public IActionResult UpdateBook(int id, Book book)
        {
            book.Id = id;

            bool updated = service.UpdateBook(book);

            if (!updated)
            {
                return NotFound("Book not found.");
            }

            return Ok("Book updated successfully.");
        }

        [HttpDelete("{id}")]
        public IActionResult DeleteBook(int id)
        {
            bool deleted = service.DeleteBook(id);

            if (!deleted)
            {
                return NotFound("Book not found.");
            }

            return Ok("Book deleted successfully.");
        }
    }
}