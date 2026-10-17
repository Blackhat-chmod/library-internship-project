using System.Net;
using System.Net.Http.Json;
using LibraryApi.Data;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace LibraryApi.Tests;

public class ReservationsIntegrationTests
{
    [Fact]
    public async Task Reserve_WithoutAuthentication_Returns401()
    {
        using CustomWebApplicationFactory factory = new();

        using HttpClient client = factory.CreateClient();

        using HttpRequestMessage request =
            new(
                HttpMethod.Post,
                "/api/books/1001/reserve"
            );

        request.Headers.Add(
            "Idempotency-Key",
            "week7-unauthenticated"
        );

        HttpResponseMessage response =
            await client.SendAsync(request);

        Assert.Equal(
            HttpStatusCode.Unauthorized,
            response.StatusCode
        );
    }

    [Fact]
    public async Task Reserve_WithoutIdempotencyKey_Returns400()
    {
        using CustomWebApplicationFactory factory = new();

        using HttpClient client = CreateAuthenticatedClient(
            factory
        );

        HttpResponseMessage response =
            await client.PostAsync(
                "/api/books/1001/reserve",
                null
            );

        Assert.Equal(
            HttpStatusCode.BadRequest,
            response.StatusCode
        );
    }

    [Fact]
    public async Task Reserve_MissingBook_Returns404()
    {
        using CustomWebApplicationFactory factory = new();

        using HttpClient client = CreateAuthenticatedClient(
            factory
        );

        using HttpRequestMessage request =
            CreateReserveRequest(
                999999,
                "week7-missing-book"
            );

        HttpResponseMessage response =
            await client.SendAsync(request);

        Assert.Equal(
            HttpStatusCode.NotFound,
            response.StatusCode
        );
    }

    [Fact]
    public async Task Reserve_UnavailableBook_Returns409()
    {
        using CustomWebApplicationFactory factory = new();

        using HttpClient client = CreateAuthenticatedClient(
            factory
        );

        using HttpRequestMessage request =
            CreateReserveRequest(
                1002,
                "week7-unavailable-book"
            );

        HttpResponseMessage response =
            await client.SendAsync(request);

        Assert.Equal(
            HttpStatusCode.Conflict,
            response.StatusCode
        );
    }

    [Fact]
    public async Task Reserve_AvailableBook_CreatesReservation()
    {
        using CustomWebApplicationFactory factory = new();

        using HttpClient client = CreateAuthenticatedClient(
            factory
        );

        using HttpRequestMessage request =
            CreateReserveRequest(
                1001,
                "week7-create-reservation"
            );

        HttpResponseMessage response =
            await client.SendAsync(request);

        Assert.Equal(
            HttpStatusCode.OK,
            response.StatusCode
        );

        ReservationResponse? body =
            await response.Content
                .ReadFromJsonAsync<ReservationResponse>();

        Assert.NotNull(body);
        Assert.Equal(1001, body.BookId);
        Assert.False(body.Replayed);

        using IServiceScope scope =
            factory.Services.CreateScope();

        LibraryDbContext context =
            scope.ServiceProvider
                .GetRequiredService<LibraryDbContext>();

        Assert.Equal(
            1,
            context.Reservations.Count()
        );

        Assert.False(
            context.Books
                .Single(book => book.BookId == 1001)
                .IsAvailable
        );
    }

    [Fact]
    public async Task Reserve_SameIdempotencyKeyTwice_CreatesOneReservation()
    {
        using CustomWebApplicationFactory factory = new();

        using HttpClient client = CreateAuthenticatedClient(
            factory
        );

        const string idempotencyKey =
            "week7-idempotency-test";

        using HttpRequestMessage firstRequest =
            CreateReserveRequest(
                1001,
                idempotencyKey
            );

        HttpResponseMessage firstResponse =
            await client.SendAsync(firstRequest);

        Assert.Equal(
            HttpStatusCode.OK,
            firstResponse.StatusCode
        );

        ReservationResponse? firstBody =
            await firstResponse.Content
                .ReadFromJsonAsync<ReservationResponse>();

        Assert.NotNull(firstBody);
        Assert.False(firstBody.Replayed);

        using HttpRequestMessage secondRequest =
            CreateReserveRequest(
                1001,
                idempotencyKey
            );

        HttpResponseMessage secondResponse =
            await client.SendAsync(secondRequest);

        Assert.Equal(
            HttpStatusCode.OK,
            secondResponse.StatusCode
        );

        ReservationResponse? secondBody =
            await secondResponse.Content
                .ReadFromJsonAsync<ReservationResponse>();

        Assert.NotNull(secondBody);
        Assert.True(secondBody.Replayed);

        Assert.Equal(
            firstBody.Id,
            secondBody.Id
        );

        using IServiceScope scope =
            factory.Services.CreateScope();

        LibraryDbContext context =
            scope.ServiceProvider
                .GetRequiredService<LibraryDbContext>();

        Assert.Equal(
            1,
            context.Reservations.Count()
        );
    }

    [Fact]
    public async Task GetMyReservations_ReturnsOnlyAuthenticatedUsersReservations()
    {
        using CustomWebApplicationFactory factory = new();

        using HttpClient client = CreateAuthenticatedClient(
            factory
        );

        using HttpRequestMessage reserveRequest =
            CreateReserveRequest(
                1001,
                "week7-my-reservations"
            );

        HttpResponseMessage reserveResponse =
            await client.SendAsync(reserveRequest);

        Assert.Equal(
            HttpStatusCode.OK,
            reserveResponse.StatusCode
        );

        HttpResponseMessage response =
            await client.GetAsync(
                "/api/me/reservations"
            );

        Assert.Equal(
            HttpStatusCode.OK,
            response.StatusCode
        );

        List<MyReservationResponse>? reservations =
            await response.Content
                .ReadFromJsonAsync<
                    List<MyReservationResponse>
                >();

        Assert.NotNull(reservations);

        MyReservationResponse reservation =
            Assert.Single(reservations);

        Assert.Equal(
            1001,
            reservation.BookId
        );

        Assert.Equal(
            "Week 7 Available Book",
            reservation.Title
        );
    }

    private static HttpClient CreateAuthenticatedClient(
        CustomWebApplicationFactory factory)
    {
        HttpClient client = factory.CreateClient();

        client.DefaultRequestHeaders.Add(
            "X-Test-User-Id",
            "1"
        );

        return client;
    }

    private static HttpRequestMessage CreateReserveRequest(
        int bookId,
        string idempotencyKey)
    {
        HttpRequestMessage request =
            new(
                HttpMethod.Post,
                $"/api/books/{bookId}/reserve"
            );

        request.Headers.Add(
            "Idempotency-Key",
            idempotencyKey
        );

        return request;
    }

    private sealed class ReservationResponse
    {
        public int Id { get; set; }

        public int BookId { get; set; }

        public DateTime CreatedAt { get; set; }

        public bool Replayed { get; set; }
    }

    private sealed class MyReservationResponse
    {
        public int Id { get; set; }

        public int BookId { get; set; }

        public string Title { get; set; }
            = string.Empty;

        public DateTime CreatedAt { get; set; }
    }
}