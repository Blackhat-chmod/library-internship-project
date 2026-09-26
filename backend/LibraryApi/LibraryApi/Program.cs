using System.Text;
using LibraryApi.Data;
using LibraryApi.Repositories;
using LibraryApi.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi;
using Polly;
using Polly.Extensions.Http;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();

builder.Services.AddDbContext<LibraryDbContext>(options =>
    options.UseSqlServer(
        builder.Configuration.GetConnectionString("LibraryDb")
    ));

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        string key = builder.Configuration["Jwt:Key"]
            ?? throw new InvalidOperationException(
                "JWT key is missing."
            );

        options.TokenValidationParameters =
            new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,

                IssuerSigningKey =
                    new SymmetricSecurityKey(
                        Encoding.UTF8.GetBytes(key)
                    ),

                ValidateIssuer = true,

                ValidIssuer =
                    builder.Configuration["Jwt:Issuer"],

                ValidateAudience = true,

                ValidAudience =
                    builder.Configuration["Jwt:Audience"],

                ValidateLifetime = true,

                ClockSkew = TimeSpan.Zero
            };
    });

builder.Services.AddAuthorization();

builder.Services.AddEndpointsApiExplorer();

builder.Services.AddSwaggerGen(options =>
{
    options.AddSecurityDefinition(
        "bearer",
        new OpenApiSecurityScheme
        {
            Type = SecuritySchemeType.Http,
            Scheme = "bearer",
            BearerFormat = "JWT",
            Description = "Enter your JWT token."
        }
    );

    options.AddSecurityRequirement(
        document => new OpenApiSecurityRequirement
        {
            [
                new OpenApiSecuritySchemeReference(
                    "bearer",
                    document
                )
            ] = []
        }
    );
});

builder.Services.AddScoped<IBookRepository, BookRepository>();
builder.Services.AddScoped<IBookService, BookService>();

builder.Services
    .AddHttpClient<IAiServiceClient, AiServiceClient>(
        client =>
        {
            string baseUrl =
                builder.Configuration["AiService:BaseUrl"]
                ?? "http://127.0.0.1:8000/";

            client.BaseAddress = new Uri(baseUrl);

            client.Timeout =
                TimeSpan.FromSeconds(25);
        }
    )
    .AddPolicyHandler(
        HttpPolicyExtensions
            .HandleTransientHttpError()
            .WaitAndRetryAsync(
                retryCount: 3,
                sleepDurationProvider: retryAttempt =>
                    TimeSpan.FromSeconds(
                        Math.Pow(2, retryAttempt)
                    ),
                onRetry: (
                    outcome,
                    delay,
                    retryAttempt,
                    context
                ) =>
                {
                    Console.WriteLine(
                        $"AI retry {retryAttempt} after " +
                        $"{delay.TotalSeconds} seconds."
                    );
                }
            )
    )
    .AddPolicyHandler(
        HttpPolicyExtensions
            .HandleTransientHttpError()
            .CircuitBreakerAsync(
                handledEventsAllowedBeforeBreaking: 3,
                durationOfBreak:
                    TimeSpan.FromSeconds(30),
                onBreak: (
                    outcome,
                    breakDelay
                ) =>
                {
                    Console.WriteLine(
                        $"AI circuit opened for " +
                        $"{breakDelay.TotalSeconds} seconds."
                    );
                },
                onReset: () =>
                {
                    Console.WriteLine(
                        "AI circuit reset."
                    );
                }
            )
    );

builder.Services.AddCors(options =>
{
    options.AddPolicy(
        "AllowAngular",
        policy =>
        {
            policy
                .WithOrigins(
                    "http://localhost:4200"
                )
                .AllowAnyHeader()
                .AllowAnyMethod();
        }
    );
});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();

    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseCors("AllowAngular");

app.UseAuthentication();

app.UseAuthorization();

app.MapControllers();

app.Run();