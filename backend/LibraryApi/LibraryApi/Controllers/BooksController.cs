using LibraryApi.Models;
using LibraryApi.Services;
using Microsoft.AspNetCore.Mvc;

namespace LibraryApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class BooksController : ControllerBase
    {
        private readonly IBookService bookService;

        public BooksController(IBookService bookService)
        {
            this.bookService = bookService;
        }

        [HttpGet]
        public async Task<IActionResult> GetAllBooks()
        {
            var books = await bookService.GetAllBooksAsync();

            return Ok(books);
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> GetBookById(int id)
        {
            var book = await bookService.GetBookByIdAsync(id);

            if (book == null)
            {
                return NotFound("Book not found.");
            }

            return Ok(book);
        }

        [HttpPost]
        public async Task<IActionResult> AddBook(Book book)
        {
            if (string.IsNullOrWhiteSpace(book.Title))
            {
                return BadRequest("Title is required.");
            }

            try
            {
                var createdBook = await bookService.AddBookAsync(book);

                return CreatedAtAction(
                    nameof(GetBookById),
                    new { id = createdBook.BookId },
                    createdBook
                );
            }
            catch (Exception)
            {
                return StatusCode(
                    500,
                    "An error occurred while saving the book."
                );
            }
        }

        [HttpPut("{id}")]
        public async Task<IActionResult> UpdateBook(int id, Book book)
        {
            if (string.IsNullOrWhiteSpace(book.Title))
            {
                return BadRequest("Title is required.");
            }

            book.BookId = id;

            try
            {
                bool updated = await bookService.UpdateBookAsync(book);

                if (!updated)
                {
                    return NotFound("Book not found.");
                }

                return Ok("Book updated successfully.");
            }
            catch (Exception)
            {
                return StatusCode(
                    500,
                    "An error occurred while updating the book."
                );
            }
        }

        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteBook(int id)
        {
            try
            {
                bool deleted = await bookService.DeleteBookAsync(id);

                if (!deleted)
                {
                    return NotFound("Book not found.");
                }

                return Ok("Book deleted successfully.");
            }
            catch (Exception)
            {
                return StatusCode(
                    500,
                    "An error occurred while deleting the book."
                );
            }
        }
    }
}