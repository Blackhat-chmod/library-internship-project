using System.Security.Claims;
using LibraryApi.Data;
using LibraryApi.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace LibraryApi.Controllers
{
    [ApiController]
    [Authorize]
    public class ReservationsController : ControllerBase
    {
        private readonly LibraryDbContext context;

        public ReservationsController(
            LibraryDbContext context)
        {
            this.context = context;
        }

        [HttpPost("api/books/{id:int}/reserve")]
        public async Task<IActionResult> ReserveBook(
            int id,
            [FromHeader(Name = "Idempotency-Key")]
            string? idempotencyKey)
        {
            int? userId = GetAuthenticatedUserId();

            if (userId == null)
            {
                return Unauthorized(
                    new
                    {
                        message = "Invalid authenticated user."
                    }
                );
            }

            if (string.IsNullOrWhiteSpace(idempotencyKey))
            {
                return BadRequest(
                    new
                    {
                        message =
                            "Idempotency-Key header is required."
                    }
                );
            }

            idempotencyKey = idempotencyKey.Trim();

            if (idempotencyKey.Length > 100)
            {
                return BadRequest(
                    new
                    {
                        message =
                            "Idempotency-Key cannot exceed 100 characters."
                    }
                );
            }

            Reservation? replay =
                await context.Reservations
                    .AsNoTracking()
                    .FirstOrDefaultAsync(
                        reservation =>
                            reservation.UserId == userId.Value &&
                            reservation.IdempotencyKey ==
                                idempotencyKey
                    );

            if (replay != null)
            {
                return Ok(
                    CreateReservationResponse(
                        replay,
                        replayed: true
                    )
                );
            }

            Book? book =
                await context.Books
                    .FirstOrDefaultAsync(
                        book => book.BookId == id
                    );

            if (book == null)
            {
                return NotFound(
                    new
                    {
                        message = "Book not found."
                    }
                );
            }

            bool alreadyReserved =
                await context.Reservations
                    .AnyAsync(
                        reservation =>
                            reservation.BookId == id &&
                            reservation.UserId ==
                                userId.Value
                    );

            if (alreadyReserved)
            {
                return Conflict(
                    new
                    {
                        message =
                            "You have already reserved this book."
                    }
                );
            }

            if (!book.IsAvailable)
            {
                return Conflict(
                    new
                    {
                        message =
                            "Book is not currently available."
                    }
                );
            }

            Reservation reservation = new Reservation
            {
                BookId = book.BookId,
                UserId = userId.Value,
                CreatedAt = DateTime.UtcNow,
                IdempotencyKey = idempotencyKey
            };

            context.Reservations.Add(reservation);

            book.IsAvailable = false;

            try
            {
                await context.SaveChangesAsync();
            }
            catch (DbUpdateException)
            {
                context.ChangeTracker.Clear();

                Reservation? existingReplay =
                    await context.Reservations
                        .AsNoTracking()
                        .FirstOrDefaultAsync(
                            existing =>
                                existing.UserId ==
                                    userId.Value &&
                                existing.IdempotencyKey ==
                                    idempotencyKey
                        );

                if (existingReplay != null)
                {
                    return Ok(
                        CreateReservationResponse(
                            existingReplay,
                            replayed: true
                        )
                    );
                }

                bool reservationExists =
                    await context.Reservations
                        .AsNoTracking()
                        .AnyAsync(
                            existing =>
                                existing.BookId == id &&
                                existing.UserId ==
                                    userId.Value
                        );

                if (reservationExists)
                {
                    return Conflict(
                        new
                        {
                            message =
                                "You have already reserved this book."
                        }
                    );
                }

                return Conflict(
                    new
                    {
                        message =
                            "The reservation could not be completed."
                    }
                );
            }

            return Ok(
                CreateReservationResponse(
                    reservation,
                    replayed: false
                )
            );
        }

        [HttpGet("api/me/reservations")]
        public async Task<IActionResult> GetMyReservations()
        {
            int? userId = GetAuthenticatedUserId();

            if (userId == null)
            {
                return Unauthorized(
                    new
                    {
                        message = "Invalid authenticated user."
                    }
                );
            }

            var reservations =
                await context.Reservations
                    .AsNoTracking()
                    .Where(
                        reservation =>
                            reservation.UserId ==
                                userId.Value
                    )
                    .OrderByDescending(
                        reservation =>
                            reservation.CreatedAt
                    )
                    .Select(
                        reservation => new
                        {
                            id = reservation.Id,
                            bookId = reservation.BookId,
                            title = reservation.Book != null
                                ? reservation.Book.Title
                                : string.Empty,
                            createdAt =
                                reservation.CreatedAt
                        }
                    )
                    .ToListAsync();

            return Ok(reservations);
        }

        private int? GetAuthenticatedUserId()
        {
            string? userIdClaim =
                User.FindFirstValue(
                    ClaimTypes.NameIdentifier
                );

            if (!int.TryParse(
                    userIdClaim,
                    out int userId))
            {
                return null;
            }

            return userId;
        }

        private static object CreateReservationResponse(
            Reservation reservation,
            bool replayed)
        {
            return new
            {
                id = reservation.Id,
                bookId = reservation.BookId,
                createdAt = reservation.CreatedAt,
                replayed
            };
        }
    }
}
