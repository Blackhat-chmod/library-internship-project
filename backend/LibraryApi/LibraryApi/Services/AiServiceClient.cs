using System.Net.Http.Json;
using LibraryApi.Models;

namespace LibraryApi.Services
{
    public class AiServiceClient : IAiServiceClient
    {
        private readonly HttpClient httpClient;
        private readonly ILogger<AiServiceClient> logger;

        public AiServiceClient(
            HttpClient httpClient,
            ILogger<AiServiceClient> logger
        )
        {
            this.httpClient = httpClient;
            this.logger = logger;
        }

        public async Task<AiAskResponse> AskAsync(
            string question,
            CancellationToken cancellationToken = default
        )
        {
            logger.LogInformation(
                "Sending question to AI service."
            );

            var request = new
            {
                question
            };

            using var response =
                await httpClient.PostAsJsonAsync(
                    "ask",
                    request,
                    cancellationToken
                );

            response.EnsureSuccessStatusCode();

            var result =
                await response.Content
                    .ReadFromJsonAsync<AiAskResponse>(
                        cancellationToken:
                            cancellationToken
                    );

            if (result == null)
            {
                throw new InvalidOperationException(
                    "AI service returned an empty response."
                );
            }

            return result;
        }
    }
}