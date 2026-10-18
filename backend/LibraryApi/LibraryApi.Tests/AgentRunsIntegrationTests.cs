using System.Net;
using System.Net.Http.Json;
using LibraryApi.Data;
using LibraryApi.Models;
using Microsoft.Extensions.DependencyInjection;

namespace LibraryApi.Tests;

public class AgentRunsIntegrationTests
    : IClassFixture<CustomWebApplicationFactory>
{
    private readonly CustomWebApplicationFactory factory;

    public AgentRunsIntegrationTests(
        CustomWebApplicationFactory factory)
    {
        this.factory = factory;
    }

    [Fact]
    public async Task GetRun_AsNonOwner_Returns404()
    {
        string threadId =
            Guid.NewGuid().ToString();

        await SeedAgentThreadAsync(
            threadId,
            ownerUserId: 1
        );

        using HttpClient client =
            CreateClientForUser(
                userId: 2
            );

        HttpResponseMessage response =
            await client.GetAsync(
                $"/api/assistant/agent/runs/{threadId}"
            );

        Assert.Equal(
            HttpStatusCode.NotFound,
            response.StatusCode
        );
    }

    [Fact]
    public async Task ResumeRun_AsNonOwner_Returns404()
    {
        string threadId =
            Guid.NewGuid().ToString();

        await SeedAgentThreadAsync(
            threadId,
            ownerUserId: 1
        );

        using HttpClient client =
            CreateClientForUser(
                userId: 2
            );

        HttpResponseMessage response =
            await client.PostAsJsonAsync(
                $"/api/assistant/agent/runs/{threadId}/resume",
                new
                {
                    approved = true
                }
            );

        Assert.Equal(
            HttpStatusCode.NotFound,
            response.StatusCode
        );
    }

    [Fact]
    public async Task CancelRun_AsNonOwner_Returns404()
    {
        string threadId =
            Guid.NewGuid().ToString();

        await SeedAgentThreadAsync(
            threadId,
            ownerUserId: 1
        );

        using HttpClient client =
            CreateClientForUser(
                userId: 2
            );

        HttpResponseMessage response =
            await client.PostAsync(
                $"/api/assistant/agent/runs/{threadId}/cancel",
                content: null
            );

        Assert.Equal(
            HttpStatusCode.NotFound,
            response.StatusCode
        );
    }

    private HttpClient CreateClientForUser(
        int userId)
    {
        HttpClient client =
            factory.CreateClient();

        client.DefaultRequestHeaders.Add(
            "X-Test-User-Id",
            userId.ToString()
        );

        return client;
    }

    private async Task SeedAgentThreadAsync(
        string threadId,
        int ownerUserId)
    {
        using IServiceScope scope =
            factory.Services.CreateScope();

        LibraryDbContext context =
            scope.ServiceProvider
                .GetRequiredService<LibraryDbContext>();

        AgentThread thread =
            new AgentThread
            {
                ThreadId = threadId,
                UserId = ownerUserId,
                CreatedAt = DateTime.UtcNow
            };

        context.AgentThreads.Add(thread);

        await context.SaveChangesAsync();
    }
}