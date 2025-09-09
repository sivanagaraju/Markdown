Understand Systems Thinking
Contributed by Charles Humble

Difficulty level: Intermediate

It is surprisingly easy to get trapped in ways of thinking that limit your ability to progress.

When I started writing code as a teenager in the early 1980s on my trusty Commodore 64, the programs I created were linear and easy enough to reason about. I didn’t know it at the time but in hindsight I was learning a specific approach to thinking about software. That approach is reductionism, which I’m going to summarize as the idea that a complex system is just the sum of its parts.

Around the same time, I also started writing music. One of the things that I realized when I joined my first band was that all of my best music was created as part of a small team, typically three or four of us, and that that was also true for my band members. We could all write decent songs on our own, but they were somehow never as good as when we wrote them as a group. Musicians often talk about how the “sum is greater than the parts” and having written music for about 40 years, it remains the case for me.

I didn’t link this insight to my professional work until much later.

My early professional programming jobs involved working in a single monolithic enterprise codebase in an equally linear fashion to my early programs. Using reductionism to reason about the software I was building worked well for me. It stopped doing so when I started coding on my first distributed system, building an internet banking app for a UK High Street bank in the early 2000s.

While in that role, we used a series of message queues with a set of small programs that read the messages off the queues and attempted to process them. These programs were put together in a variety of combinations to build services like “Get Balances.” The individual programs, which we called elements, were short and easy to reason about. Each was single-threaded, but multiple instances could be run simultaneously to service a single queue. All the complexity was in how the elements worked together.

The majority of modern software is built up the same way, from a set of event-driven, interdependently deployable services that can evolve at different rates. While the skills we learn through reductionism are still useful when creating an individual service, they fail us when we try to reason about the system as a whole.

This is where systems thinking comes in.

Systems thinking is about paying attention to the relationships between things. In Thinking in Systems, Donella Meadows says, “You think that because you understand ‘one’ that you must therefore understand ‘two’ because one and one make two. But you forget that you must also understand ‘and’.”

A quality of distributed systems like microservices is that we get emergent behaviors that are a consequence of how the services interact. Our systems are not the sum of their parts but more the product of their interactions. We want the whole to be stable and coherent even though different parts can evolve at different rates. This necessitates a shift in our thinking to focus less on the individual services and more on the relationships and patterns between them.

To shift your thinking, you first need to develop habits to understand your existing thought patterns—a process called metacognition.

Some ideas we looked at in the Shortcut on problem solving apply equally here. Talking through your idea with someone else—essentially “rubberducking” or confessional programming, but for ideas rather than bugs—can be helpful. Likewise, going for a walk is useful because, as we explored before, it helps your brain switch into a different mode.

Get into the habit of writing down any idea that seems interesting. It is surprising, and somewhat unnerving, how often a concept that seems brilliant in your head turns to dust on paper.

Creating art of any sort is also helpful. I don’t think it is important how good the art is. The skills you use to create are helpful in other ways. For me, personally, the practice of writing music—which is one of constant decision making, choosing which ideas to include and which to reject in the pursuit of a piece that feels like a coherent whole—also helps when I’m reasoning about software systems.

The second thing you need to do is focus on the interactions, whether of teams, organizations, or software systems.

If you want to work effectively as a team, you need to learn how to communicate and solve problems as a group rather than individually. Working this way helps when dealing with the inevitable uncertainty that arises as our systems get ever more complex.

A few years ago I worked as the architect for a start-up where we had on-shored about 16 Java developers from India to London. They were mostly quite junior. Having mainly worked with developers from the UK and US, one of the things that I found hard was that the Indian developers were reluctant to challenge me. The breakthrough came when I said to them, “I cannot be an expert in everything. None of us can be. If we are going to succeed, we have to share our knowledge and expertise.”

In systems thinking, both the software and the role of a leader may change. As Diana Montalion puts it in Learning Systems Thinking, “My role as a systems architect is to synthesize ideas, not dictate what to think. My goal is to empower people to thrive because I depend on everyone’s knowledge to succeed (just like the system).”

Get into the habit of showing your work for example, “Here is my recommendation, and this is how I arrived at it. Can you help me improve it?” Doing this allows others to understand how you got there, learn from you, and challenge you.

It is the relationships between your services and the people who build them that you should focus on as you become more senior.