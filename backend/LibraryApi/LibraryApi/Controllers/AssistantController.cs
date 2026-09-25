using LibraryApi.Models;
using LibraryApi.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Polly.CircuitBreaker;

namespace LibraryApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class AssistantController : ControllerBase
    {
        private readonly IAiServiceClient aiServiceClient;
        private readonly ILogger<AssistantController> logger;

        public AssistantController(
            IAiServiceClient aiServiceClient,
            ILogger<AssistantController> logger
        )
        {
            this.aiServiceClient = aiServiceClient;
            this.logger = logger;
        }

        [HttpPost("ask")]
        public async Task<IActionResult> Ask(
            AskDto dto,
            CancellationToken cancellationToken
        )
        {
            if (string.IsNullOrWhiteSpace(dto.Question))
            {
                return BadRequest(
                    new
                    {
                        message = "Question is required."
                    }
                );
            }

            try
            {
                var result =
                    await aiServiceClient.AskAsync(
                        dto.Question,
                        cancellationToken
                    );

                return Ok(result);
            }
            catch (BrokenCircuitException)
            {
                logger.LogWarning(
                    "AI service circuit breaker is open."
                );

                return StatusCode(
                    StatusCodes.Status503ServiceUnavailable,
                    new
                    {
                        message =
                            "The AI assistant is temporarily unavailable. Please try again shortly."
                    }
                );
            }
            catch (HttpRequestException exception)
            {
                logger.LogError(
                    exception,
                    "AI service request failed."
                );

                return StatusCode(
                    StatusCodes.Status503ServiceUnavailable,
                    new
                    {
                        message =
                            "The AI assistant is temporarily unavailable. Please try again shortly."
                    }
                );
            }
            catch (TaskCanceledException exception)
            {
                logger.LogWarning(
                    exception,
                    "AI service request timed out."
                );

                return StatusCode(
                    StatusCodes.Status503ServiceUnavailable,
                    new
                    {
                        message =
                            "The AI assistant did not respond in time. Please try again shortly."
                    }
                );
            }
        }
    }
}