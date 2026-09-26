using System.Net.Http.Json;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LibraryApi.Controllers
{
    [ApiController]
    [Route("api/assistant")]
    [Authorize]
    public class AssistantStreamController : ControllerBase
    {
        private readonly IHttpClientFactory httpClientFactory;
        private readonly ILogger<AssistantStreamController> logger;

        public AssistantStreamController(
            IHttpClientFactory httpClientFactory,
            ILogger<AssistantStreamController> logger
        )
        {
            this.httpClientFactory = httpClientFactory;
            this.logger = logger;
        }

        public class StreamAskRequest
        {
            public string Question { get; set; } = string.Empty;

            public int DelayMs { get; set; } = 0;
        }

        [HttpPost("ask/stream")]
        public async Task AskStream(
            StreamAskRequest request,
            CancellationToken cancellationToken
        )
        {
            if (string.IsNullOrWhiteSpace(request.Question))
            {
                Response.StatusCode =
                    StatusCodes.Status400BadRequest;

                await Response.WriteAsJsonAsync(
                    new
                    {
                        message = "Question is required."
                    },
                    cancellationToken
                );

                return;
            }

            var client =
                httpClientFactory.CreateClient(
                    "AiStreamingClient"
                );

            using var fastApiRequest =
                new HttpRequestMessage(
                    HttpMethod.Post,
                    "ask/stream"
                );

            fastApiRequest.Content =
                JsonContent.Create(
                    new
                    {
                        question =
                            request.Question,
                        delay_ms =
                            request.DelayMs
                    }
                );

            try
            {
                using var fastApiResponse =
                    await client.SendAsync(
                        fastApiRequest,
                        HttpCompletionOption.ResponseHeadersRead,
                        cancellationToken
                    );

                if (!fastApiResponse.IsSuccessStatusCode)
                {
                    logger.LogWarning(
                        "FastAPI streaming endpoint returned {StatusCode}.",
                        fastApiResponse.StatusCode
                    );

                    Response.StatusCode =
                        StatusCodes.Status502BadGateway;

                    await Response.WriteAsJsonAsync(
                        new
                        {
                            message =
                                "The AI streaming service returned an error."
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
                    !reader.EndOfStream &&
                    !cancellationToken
                        .IsCancellationRequested
                )
                {
                    var line =
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
                    "Streaming request was cancelled by the client."
                );
            }
            catch (HttpRequestException exception)
            {
                logger.LogError(
                    exception,
                    "Could not reach the FastAPI streaming service."
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
                                "The AI streaming service is temporarily unavailable."
                        },
                        cancellationToken
                    );
                }
            }
        }
    }
}