using System.Net;
using System.Net.Http.Json;
using System.Security.Claims;
using LibraryApi.Data;
using LibraryApi.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;

namespace LibraryApi.Controllers
{
    [ApiController]
    [Route("api/assistant/agent/runs")]
    [Authorize]
    [EnableRateLimiting("AssistantAgentPolicy")]
    public class AgentRunsController : ControllerBase
    {
        private readonly LibraryDbContext dbContext;
        private readonly IHttpClientFactory httpClientFactory;
        private readonly IConfiguration configuration;
        private readonly ILogger<AgentRunsController> logger;

        public AgentRunsController(
            LibraryDbContext dbContext,
            IHttpClientFactory httpClientFactory,
            IConfiguration configuration,
            ILogger<AgentRunsController> logger
        )
        {
            this.dbContext = dbContext;
            this.httpClientFactory = httpClientFactory;
            this.configuration = configuration;
            this.logger = logger;
        }

        public class StartAgentRunRequest
        {
            public string Message { get; set; } = string.Empty;
        }

        public class ResumeAgentRunRequest
        {
            public bool Approved { get; set; }
        }

        [HttpPost]
        public async Task StartRun(
            StartAgentRunRequest request,
            CancellationToken cancellationToken
        )
        {
            if (string.IsNullOrWhiteSpace(request.Message))
            {
                Response.StatusCode =
                    StatusCodes.Status400BadRequest;

                await Response.WriteAsJsonAsync(
                    new
                    {
                        message = "Message is required."
                    },
                    cancellationToken
                );

                return;
            }

            if (request.Message.Length > 1000)
            {
                Response.StatusCode =
                    StatusCodes.Status400BadRequest;

                await Response.WriteAsJsonAsync(
                    new
                    {
                        message =
                            "Message cannot exceed 1000 characters."
                    },
                    cancellationToken
                );

                return;
            }

            int userId = GetAuthenticatedUserId();

            string threadId =
                Guid.NewGuid().ToString();

            var agentThread =
                new AgentThread
                {
                    ThreadId = threadId,
                    UserId = userId,
                    CreatedAt = DateTime.UtcNow
                };

            dbContext.AgentThreads.Add(
                agentThread
            );

            await dbContext.SaveChangesAsync(
                cancellationToken
            );

            using var fastApiRequest =
                CreateFastApiRequest(
                    HttpMethod.Post,
                    "agent/runs"
                );

            fastApiRequest.Content =
                JsonContent.Create(
                    new
                    {
                        message = request.Message,
                        threadId
                    }
                );

            await ProxyStreamingResponse(
                fastApiRequest,
                cancellationToken
            );
        }

        [HttpPost("{threadId}/resume")]
        public async Task ResumeRun(
            string threadId,
            ResumeAgentRunRequest request,
            CancellationToken cancellationToken
        )
        {
            int userId =
                GetAuthenticatedUserId();

            bool ownsThread =
                await dbContext.AgentThreads
                    .AsNoTracking()
                    .AnyAsync(
                        thread =>
                            thread.ThreadId ==
                                threadId &&
                            thread.UserId ==
                                userId,
                        cancellationToken
                    );

            if (!ownsThread)
            {
                Response.StatusCode =
                    StatusCodes.Status404NotFound;

                await Response.WriteAsJsonAsync(
                    new
                    {
                        message =
                            "Agent thread was not found."
                    },
                    cancellationToken
                );

                return;
            }

            using var fastApiRequest =
                CreateFastApiRequest(
                    HttpMethod.Post,
                    $"agent/runs/{threadId}/resume"
                );

            string idempotencyKey =
                $"agent-{threadId}";

            fastApiRequest.Headers.TryAddWithoutValidation(
                "Idempotency-Key",
                idempotencyKey
            );

            fastApiRequest.Content =
                JsonContent.Create(
                    new
                    {
                        approved =
                            request.Approved
                    }
                );

            await ProxyStreamingResponse(
                fastApiRequest,
                cancellationToken
            );
        }

        [HttpGet("{threadId}")]
        public async Task<IActionResult> GetRun(
            string threadId,
            CancellationToken cancellationToken
        )
        {
            int userId =
                GetAuthenticatedUserId();

            bool ownsThread =
                await dbContext.AgentThreads
                    .AsNoTracking()
                    .AnyAsync(
                        thread =>
                            thread.ThreadId ==
                                threadId &&
                            thread.UserId ==
                                userId,
                        cancellationToken
                    );

            if (!ownsThread)
            {
                return NotFound(
                    new
                    {
                        message =
                            "Agent thread was not found."
                    }
                );
            }

            using var fastApiRequest =
                CreateFastApiRequest(
                    HttpMethod.Get,
                    $"agent/runs/{threadId}"
                );

            var client =
                httpClientFactory.CreateClient(
                    "AiAgentClient"
                );

            try
            {
                using var fastApiResponse =
                    await client.SendAsync(
                        fastApiRequest,
                        HttpCompletionOption
                            .ResponseHeadersRead,
                        cancellationToken
                    );

                if (
                    fastApiResponse.StatusCode ==
                    HttpStatusCode.NotFound
                )
                {
                    return NotFound(
                        new
                        {
                            message =
                                "Agent thread state was not found."
                        }
                    );
                }

                if (!fastApiResponse.IsSuccessStatusCode)
                {
                    logger.LogWarning(
                        "FastAPI agent status returned {StatusCode}.",
                        fastApiResponse.StatusCode
                    );

                    return StatusCode(
                        StatusCodes
                            .Status502BadGateway,
                        new
                        {
                            message =
                                "The AI agent service returned an error."
                        }
                    );
                }

                string content =
                    await fastApiResponse.Content
                        .ReadAsStringAsync(
                            cancellationToken
                        );

                return Content(
                    content,
                    "application/json"
                );
            }
            catch (OperationCanceledException)
                when (
                    cancellationToken
                        .IsCancellationRequested
                )
            {
                return StatusCode(
                    499,
                    new
                    {
                        message =
                            "Request was cancelled."
                    }
                );
            }
            catch (HttpRequestException exception)
            {
                logger.LogError(
                    exception,
                    "Could not reach FastAPI agent status endpoint."
                );

                return StatusCode(
                    StatusCodes
                        .Status503ServiceUnavailable,
                    new
                    {
                        message =
                            "The AI agent service is temporarily unavailable."
                    }
                );
            }
        }

        [HttpPost("{threadId}/cancel")]
        public async Task<IActionResult> CancelRun(
            string threadId,
            CancellationToken cancellationToken
        )
        {
            int userId =
                GetAuthenticatedUserId();

            bool ownsThread =
                await dbContext.AgentThreads
                    .AsNoTracking()
                    .AnyAsync(
                        thread =>
                            thread.ThreadId ==
                                threadId &&
                            thread.UserId ==
                                userId,
                        cancellationToken
                    );

            if (!ownsThread)
            {
                return NotFound(
                    new
                    {
                        message =
                            "Agent thread was not found."
                    }
                );
            }

            using var fastApiRequest =
                CreateFastApiRequest(
                    HttpMethod.Post,
                    $"agent/runs/{threadId}/cancel"
                );

            var client =
                httpClientFactory.CreateClient(
                    "AiAgentClient"
                );

            try
            {
                using var fastApiResponse =
                    await client.SendAsync(
                        fastApiRequest,
                        cancellationToken
                    );

                if (
                    fastApiResponse.StatusCode ==
                    HttpStatusCode.NotFound
                )
                {
                    return NotFound(
                        new
                        {
                            message =
                                "Agent thread state was not found."
                        }
                    );
                }

                if (!fastApiResponse.IsSuccessStatusCode)
                {
                    logger.LogWarning(
                        "FastAPI agent cancel returned {StatusCode}.",
                        fastApiResponse.StatusCode
                    );

                    return StatusCode(
                        StatusCodes
                            .Status502BadGateway,
                        new
                        {
                            message =
                                "The AI agent service returned an error."
                        }
                    );
                }

                string content =
                    await fastApiResponse.Content
                        .ReadAsStringAsync(
                            cancellationToken
                        );

                return Content(
                    content,
                    "application/json"
                );
            }
            catch (OperationCanceledException)
                when (
                    cancellationToken
                        .IsCancellationRequested
                )
            {
                return StatusCode(
                    499,
                    new
                    {
                        message =
                            "Request was cancelled."
                    }
                );
            }
            catch (HttpRequestException exception)
            {
                logger.LogError(
                    exception,
                    "Could not reach FastAPI agent cancel endpoint."
                );

                return StatusCode(
                    StatusCodes
                        .Status503ServiceUnavailable,
                    new
                    {
                        message =
                            "The AI agent service is temporarily unavailable."
                    }
                );
            }
        }

        private HttpRequestMessage CreateFastApiRequest(
            HttpMethod method,
            string relativeUrl
        )
        {
            string serviceKey =
                configuration[
                    "AiService:ServiceKey"
                ]
                ?? string.Empty;

            if (string.IsNullOrWhiteSpace(serviceKey))
            {
                throw new InvalidOperationException(
                    "AI service key is not configured."
                );
            }

            string? authorization =
                Request.Headers.Authorization
                    .FirstOrDefault();

            if (
                string.IsNullOrWhiteSpace(
                    authorization
                )
            )
            {
                throw new InvalidOperationException(
                    "Authenticated user token is missing."
                );
            }

            var request =
                new HttpRequestMessage(
                    method,
                    relativeUrl
                );

            request.Headers.TryAddWithoutValidation(
                "X-Service-Key",
                serviceKey
            );

            request.Headers.TryAddWithoutValidation(
                "Authorization",
                authorization
            );

            return request;
        }

        private async Task ProxyStreamingResponse(
            HttpRequestMessage fastApiRequest,
            CancellationToken cancellationToken
        )
        {
            var client =
                httpClientFactory.CreateClient(
                    "AiAgentClient"
                );

            try
            {
                using var fastApiResponse =
                    await client.SendAsync(
                        fastApiRequest,
                        HttpCompletionOption
                            .ResponseHeadersRead,
                        cancellationToken
                    );

                if (!fastApiResponse.IsSuccessStatusCode)
                {
                    logger.LogWarning(
                        "FastAPI agent endpoint returned {StatusCode}.",
                        fastApiResponse.StatusCode
                    );

                    Response.StatusCode =
                        fastApiResponse.StatusCode ==
                        HttpStatusCode
                            .TooManyRequests
                        ? StatusCodes
                            .Status429TooManyRequests
                        : StatusCodes
                            .Status502BadGateway;

                    await Response.WriteAsJsonAsync(
                        new
                        {
                            message =
                                "The AI agent service returned an error."
                        },
                        cancellationToken
                    );

                    return;
                }

                Response.StatusCode =
                    StatusCodes.Status200OK;

                Response.ContentType =
                    "text/event-stream";

                Response.Headers.CacheControl =
                    "no-cache";

                Response.Headers.Append(
                    "X-Accel-Buffering",
                    "no"
                );

                await Response.StartAsync(
                    cancellationToken
                );

                await using var stream =
                    await fastApiResponse.Content
                        .ReadAsStreamAsync(
                            cancellationToken
                        );

                using var reader =
                    new StreamReader(stream);

                while (
                    !cancellationToken
                        .IsCancellationRequested
                )
                {
                    string? line =
                        await reader.ReadLineAsync(
                            cancellationToken
                        );

                    if (line == null)
                    {
                        break;
                    }

                    await Response.WriteAsync(
                        line + "\n",
                        cancellationToken
                    );

                    if (line.Length == 0)
                    {
                        await Response.Body
                            .FlushAsync(
                                cancellationToken
                            );
                    }
                }
            }
            catch (OperationCanceledException)
            {
                logger.LogInformation(
                    "Agent streaming request ended or was cancelled."
                );
            }
            catch (HttpRequestException exception)
            {
                logger.LogError(
                    exception,
                    "Could not reach the FastAPI agent service."
                );

                if (!Response.HasStarted)
                {
                    Response.StatusCode =
                        StatusCodes
                            .Status503ServiceUnavailable;

                    await Response.WriteAsJsonAsync(
                        new
                        {
                            message =
                                "The AI agent service is temporarily unavailable."
                        },
                        cancellationToken
                    );
                }
            }
        }

        private int GetAuthenticatedUserId()
        {
            string? userIdValue =
                User.FindFirstValue(
                    ClaimTypes.NameIdentifier
                );

            if (
                !int.TryParse(
                    userIdValue,
                    out int userId
                )
            )
            {
                throw new UnauthorizedAccessException(
                    "Authenticated user ID is invalid."
                );
            }

            return userId;
        }
    }
}