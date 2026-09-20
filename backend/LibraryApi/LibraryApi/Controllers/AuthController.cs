using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using LibraryApi.Data;
using LibraryApi.Models;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;

namespace LibraryApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class AuthController : ControllerBase
    {
        private readonly LibraryDbContext context;
        private readonly IConfiguration configuration;

        public AuthController(
            LibraryDbContext context,
            IConfiguration configuration)
        {
            this.context = context;
            this.configuration = configuration;
        }

        [HttpPost("register")]
        public async Task<IActionResult> Register(RegisterRequest request)
        {
            if (string.IsNullOrWhiteSpace(request.Name) ||
                string.IsNullOrWhiteSpace(request.Email) ||
                string.IsNullOrWhiteSpace(request.Password))
            {
                return BadRequest("Name, email and password are required.");
            }

            bool exists = await context.Users
                .AnyAsync(u => u.Email == request.Email);

            if (exists)
            {
                return BadRequest("Email already exists.");
            }

            User user = new User
            {
                Name = request.Name,
                Email = request.Email,
                Role = "User"
            };

            PasswordHasher<User> hasher = new PasswordHasher<User>();

            user.PasswordHash = hasher.HashPassword(
                user,
                request.Password
            );

            context.Users.Add(user);
            await context.SaveChangesAsync();

            return Ok(new
            {
                message = "User registered successfully."
            });
        }

        [HttpPost("login")]
        public async Task<IActionResult> Login(LoginRequest request)
        {
            User? user = await context.Users
                .FirstOrDefaultAsync(u => u.Email == request.Email);

            if (user == null)
            {
                return Unauthorized("Invalid email or password.");
            }

            PasswordHasher<User> hasher = new PasswordHasher<User>();

            PasswordVerificationResult result =
                hasher.VerifyHashedPassword(
                    user,
                    user.PasswordHash,
                    request.Password
                );

            if (result == PasswordVerificationResult.Failed)
            {
                return Unauthorized("Invalid email or password.");
            }

            string token = GenerateJwtToken(user);

            return Ok(new
            {
                token,
                userId = user.UserId,
                name = user.Name,
                email = user.Email,
                role = user.Role
            });
        }

        private string GenerateJwtToken(User user)
        {
            string key = configuration["Jwt:Key"]
                         ?? throw new InvalidOperationException(
                             "JWT key is missing."
                         );

            List<Claim> claims = new List<Claim>
            {
                new Claim(
                    ClaimTypes.NameIdentifier,
                    user.UserId.ToString()
                ),
                new Claim(
                    ClaimTypes.Name,
                    user.Email
                ),
                new Claim(
                    ClaimTypes.Role,
                    user.Role
                )
            };

            SymmetricSecurityKey securityKey =
                new SymmetricSecurityKey(
                    Encoding.UTF8.GetBytes(key)
                );

            SigningCredentials credentials =
                new SigningCredentials(
                    securityKey,
                    SecurityAlgorithms.HmacSha256
                );

            JwtSecurityToken token =
                new JwtSecurityToken(
                    issuer: configuration["Jwt:Issuer"],
                    audience: configuration["Jwt:Audience"],
                    claims: claims,
                    expires: DateTime.UtcNow.AddMinutes(
                        double.Parse(
                            configuration["Jwt:ExpiryMinutes"] ?? "60"
                        )
                    ),
                    signingCredentials: credentials
                );

            return new JwtSecurityTokenHandler()
                .WriteToken(token);
        }
    }
}