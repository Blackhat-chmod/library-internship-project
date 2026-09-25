using LibraryApi.Models;

namespace LibraryApi.Services
{
    public interface IAiServiceClient
    {
        Task<AiAskResponse> AskAsync(
            string question,
            CancellationToken cancellationToken = default
        );
    }
}