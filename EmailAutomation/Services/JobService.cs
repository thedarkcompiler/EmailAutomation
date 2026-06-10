using Hangfire;

namespace EmailAutomation.Services;

public class JobService : IJobService
{
    public void CreateJob()
    {
        BackgroundJob.Enqueue(() => Console.WriteLine("Hello world!"));
    }
}