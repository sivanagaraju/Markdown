Improve Your Technical Diagrams
Contributed by Charles Humble

Difficulty level: Easy

As someone who makes a living largely as a writer, I feel that “natural” language (that has been developed for people rather than for computers) is a maddeningly ambiguous means of communication. Conversely, the code we write as programmers is extremely detailed and precise. Used well, diagrams provide a helpful middle ground where you gain greater clarity than you can achieve from natural language alone, and you can focus on the important points without getting bogged down in minutiae.

Simon Brown, software architecture consultant and creator of the C4 model, has noted that, unfortunately, “Many software development teams have lost the ability to communicate visually.” Brown thinks this may be a side effect of the race to agility. I suspect the difficulty of keeping diagrams up to date, particularly with rapidly changing microservices systems, has compounded the problem.

Whatever the reason, we end up with diagrams that have a mixture of colors and shapes for no discernible reason—boxes without lines; acronyms without explanations; and a mixture of horizontal and vertical layers. None of them convey meaning effectively.

We’re engineers, of course, not artists, so in this Shortcut we’ll look at some of the key techniques you can use, including Brown’s C4 model and UML, alongside practical advice for how and when to use diagrams, and how to maintain them.

Standard Notion and Abstraction
A recurring theme of this Shortcut series is the importance of knowing who your audience is. There are many different audiences for your architecture diagrams, including software architects and developers, operations and support staff, testers, product owners, users, management, business sponsors, potential investors, and more. Thinking about who the diagram is for is vital in order to achieve the right level of abstraction.

Brown and I both believe that abstraction is more important than notation. However, if you are completely new to the topic, learning a standard notation is helpful. While there are alternatives including ArchiMate and SysML for developers working with object-oriented programming languages, Unified Modelling Language (UML) is where I recommend you start. It has become unfashionable due to perceived complexity, which feels at odds with the agility of modern software engineering, but I believe spending some time learning the basics of UML will pay dividends at both an individual and team level:

At the team level, good software architecture diagrams assist with communication when onboarding new staff, communication both within the software development team and outside it, threat modeling, and risk identification.

Having a method for diagramming as a programmer provides you with another tool to use when exploring a problem domain. Despite my lack of artistic talent, I frequently hand-draw UML diagrams (particularly sequence and state diagrams) as a way of clarifying my thinking before I start coding. Doing so helps me identify issues I’ve not yet considered and saves time when I’m coding.

I suspect one of the reasons UML has fallen out of favor is because it can appear quite daunting, but Martin Fowler’s classic text, UML Distilled, can get you up to speed with the basics in a couple of days. There are four main diagram types I’d recommend starting with:

Class diagrams
These describe the types of objects in the system and the various static relationships between them.

Interaction and sequence diagrams
These describe how groups of objects collaborate in some behavior.

State diagrams
These describe all the possible states that an object can get into and how the object’s state changes as a result of events.

Activity diagrams
These are a variation on a state diagram that describe the sequencing of activities and support both conditional and parallel behavior. They are particularly useful for describing workflows.

If you are drawing upon use cases as a way to tie together different scenarios to create a common user goal, you may find use case diagrams helpful (although you don’t need to draw a diagram to utilize use cases).

Once you have some basic UML under your belt, I recommend looking at Simon Brown’s C4 model, which includes an entire section on diagramming that is abstraction-first and notation independent.

Brown breaks down a software system into a hierarchical series of containers (not in the Docker sense but, for example, a client-side web app, mobile app, microservice, or database schema), each of which contains one or more components which are, in turn, implemented by one or more code elements.

He favors more explanatory text than you typically see in architecture diagrams, which helps make them more explicit and easier to grasp; I think it’s a very useful approach. As a quick start you might like to watch his 2019 talk from Agile on the Beach.

Diagramming Tips
I noted earlier that the purpose of our diagrams is to focus on the important details. Given this, I tend to favor hand-drawn diagrams over those generated automatically from the code. However, there is a problem—they go out of date very quickly. This is particularly true for microservices architectures. If you are working on such systems, focus on providing a starting point to help someone figure out where to look more closely at a system.

You want your diagrams to stand on their own; they are not useful if they only make sense if you are talking someone through them. Any narrative should complement the diagram rather than explaining it.

When you are drafting your diagram, start by focusing on the content; think about layout and aesthetics only once you’ve got a first draft you are happy with. As Brown puts it, “use shape and color to complement a diagram that already makes sense.”

As you refine your diagrams:

Make sure your images have titles.
These should include the diagram’s type and scope, and be numbered if chronology is important.

Watch out for clutter.
An overcrowded diagram with criss-crossing arrows, missing labels, or text that requires a magnifying glass to read is a hindrance, not a help.

Aim for visual consistency.
Across diagrams, be consistent with notation, colors, and the positioning of objects.

Use lines to show important dependencies and data flows.
Favor unidirectional lines and provide an annotation to explain the purpose of each one.

Be careful with acronyms.
With diagrams for a technical audience, you likely don’t need to explain the technical terms, but you do need to explain domain-specific acronyms as well as any code names and internal language your company uses. Diagrams aimed at a wider audience will also need to explain technical terms. When in doubt, explain it.

Include a key or legend.
This element should explain shapes, line styles, colors, borders, and acronyms, even if they seem obvious to you.

As with any writing, get into the habit of reading your diagrams out loud to see if they make sense. When you review your diagrams, ask yourself if they tell the story you want them to tell.

Think About Accessibility
Visual content can exclude readers with specific accessibility needs. Someone using a screen reader cannot “read” an image without the addition of alternative text (“alt text”) though this doesn’t necessarily mean you should always write alt text; in many cases, a better practice is to make sure the text adequately describes the image. The W3C provides a useful decision tree to help you decide when to use alt text.

Someone who is color blind may find it hard to distinguish elements of an image if the color contrast is inefficient, and sometimes your diagrams may be printed using black-and-white printers, so make sure images work if the color isn’t visible.

Some dyslexic readers will find diagrams helpful, but some (myself included) will likely not. If you are using diagrams as part of your documentation, they should be supporting but not exclusive; the text should convey as much of the information described in the diagram as possible.

For online publication, pay attention to image size; not everyone has access to fast machines and quick broadband speeds. Use a compact format such as WebP, PNG, or JPEG, and get into the habit of using an image compressor such as TinyPNG.

Finally, if you are not good at drawing diagrams, don’t be afraid to get help from someone who is. Many designers are only too grateful for freelance opportunities and can turn a badly sketched diagram into something that does a much better job of conveying the relevant information.

Mastering the art of diagramming will help you bridge the gap between ambiguous natural language and the precise code we write. By combining methods like Simon Brown’s C4 model and foundational UML techniques, you can enhance communication within your team and beyond, facilitating clearer understanding and more effective collaboration. Keep in mind that the goal is to create diagrams that convey critical information efficiently and accurately, while being mindful of accessibility and audience-specific needs. Focus on clarity, consistency, and thoughtful abstraction.