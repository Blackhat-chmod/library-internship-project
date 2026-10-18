using System.Security.Claims;
using System.Text.Encodings.Web;
using LibraryApi.Data;
using LibraryApi.Models;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace LibraryApi.Tests;

public class CustomWebApplicationFactory
    : WebApplicationFactory<Program>
{
    private SqliteConnection? connection;

    protected override void ConfigureWebHost(
        IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");

        builder.ConfigureServices(services =>
        {
            ServiceDescriptor? dbContextDescriptor =
                services.SingleOrDefault(
                    descriptor =>
                        descriptor.ServiceType ==
                        typeof(
                            IDbContextOptionsConfiguration<
                                LibraryDbContext
                            >
                        )
                );

            if (dbContextDescriptor != null)
            {
                services.Remove(dbContextDescriptor);
            }

            services.RemoveAll<
                DbContextOptions<LibraryDbContext>>();

            services.RemoveAll<LibraryDbContext>();

            connection = new SqliteConnection(
                "DataSource=:memory:"
            );

            connection.Open();

            services.AddDbContext<LibraryDbContext>(
                options =>
                {
                    options.UseSqlite(connection);
                }
            );

            services
                .AddAuthentication(options =>
                {
                    options.DefaultAuthenticateScheme =
                        TestAuthHandler.SchemeName;

                    options.DefaultChallengeScheme =
                        TestAuthHandler.SchemeName;

                    options.DefaultScheme =
                        TestAuthHandler.SchemeName;
                })
                .AddScheme<
                    AuthenticationSchemeOptions,
                    TestAuthHandler>(
                    TestAuthHandler.SchemeName,
                    _ =>
                    {
                    }
                );

            using ServiceProvider serviceProvider =
                services.BuildServiceProvider();

            using IServiceScope scope =
                serviceProvider.CreateScope();

            LibraryDbContext context =
                scope.ServiceProvider
                    .GetRequiredService<LibraryDbContext>();

            context.Database.EnsureCreated();

            SeedDatabase(context);
        });
    }

    private static void SeedDatabase(
        LibraryDbContext context)
    {
        Author author = new Author
        {
            AuthorId = 1,
            FullName = "Week 7 Test Author"
        };

        User user = new User
        {
            UserId = 1,
            Name = "Week 7 Test User",
            Email = "week7@example.test",
            PasswordHash = "not-used-in-tests",
            Role = "User"
        };

        Book availableBook = new Book
        {
            BookId = 1001,
            Title = "Week 7 Available Book",
            AuthorId = author.AuthorId,
            IsAvailable = true
        };

        Book unavailableBook = new Book
        {
            BookId = 1002,
            Title = "Week 7 Unavailable Book",
            AuthorId = author.AuthorId,
            IsAvailable = false
        };

        context.Authors.Add(author);
        context.Users.Add(user);

        context.Books.AddRange(
            availableBook,
            unavailableBook
        );

        context.SaveChanges();
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);

        if (disposing)
        {
            connection?.Dispose();
        }
    }
}

public class TestAuthHandler
    : AuthenticationHandler<AuthenticationSchemeOptions>
{
    public const string SchemeName = "Week7Test";

    public TestAuthHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder)
        : base(options, logger, encoder)
    {
    }

    protected override Task<AuthenticateResult>
        HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue(
                "X-Test-User-Id",
                out var userIdValues))
        {
            return Task.FromResult(
                AuthenticateResult.NoResult()
            );
        }

        string? userId =
            userIdValues.FirstOrDefault();

        if (string.IsNullOrWhiteSpace(userId))
        {
            return Task.FromResult(
                AuthenticateResult.Fail(
                    "Missing test user id."
                )
            );
        }

        Claim[] claims =
        {
            new Claim(
                ClaimTypes.NameIdentifier,
                userId
            ),
            new Claim(
                ClaimTypes.Name,
                "Week 7 Test User"
            ),
            new Claim(
                ClaimTypes.Role,
                "User"
            )
        };

        ClaimsIdentity identity =
            new ClaimsIdentity(
                claims,
                SchemeName
            );

        ClaimsPrincipal principal =
            new ClaimsPrincipal(identity);

        AuthenticationTicket ticket =
            new AuthenticationTicket(
                principal,
                SchemeName
            );

        return Task.FromResult(
            AuthenticateResult.Success(ticket)
        );
    }
}