Create Effective Documentation
Contributed by Charles Humble

Difficulty level: Easy

Over the last decade, as chief editor of InfoQ and then Container Solutions, I helped many engineers improve their blogging skills and realized that many of us suffer from a common affliction—fear of writing. It often starts at school when we perform less well in essay-based subjects and end up avoiding them, believing that we’re no good at writing. But fearing words, and how to use them effectively, is an encumbrance. Writing is a craft, and its principles can be learned.

What is more, words matter. When naming APIs, you know that using clear and unambiguous labels pays dividends since they are difficult to change after your API ships. A poor name—e.g., an API with DeleteFoo and RemoveFoo methods where you’ve wondered what the difference is—lives forever.

While poor API design can put your support teams under strain, bad documentation is like kryptonite. It is the gaps and ambiguities that are the hallmarks of poor documentation, and will ultimately overwhelm both you and your support team. As noted in Google’s “2021 Accelerate State of DevOps Report”, bad documentation kills projects:

“We found that documentation quality predicts teams’ success at implementing technical practices. These practices in turn predict improvements to the system’s technical capabilities, such as observability, continuous testing and deployment automation.”

Good documentation should cover everything someone using your API or product needs to know. For example, you need to spell out:

Exactly what a given API method does

What arguments it takes, and the expected values for each

What side effects are typical for this method

Every error that might be returned and how you should handle it

Of course, you won’t be able to cover everything in a single document. Just as an API should do one thing and do it well, you should avoid trying to do several things within one document. There are several types of document that you’ll likely need to write, including:

Design documents

Tutorials

Reference documentation and code comments

Each requires a slightly different approach, but there is an underlying set of common principles that we will explore in this Shortcut.

Personas and Scopes
Before you write anything—a technical doc, a blog post, a conference presentation, or a script for a podcast—start by identifying who your audience is. Knowing who you are writing for will help you to write in a way that is appropriate for your readership.

Most technology websites and marketing departments develop one or more personas to describe their audience. For your technical documentation you can, and should, do the same thing. A persona might consist of:

A role or job title such as junior programmer

An objective such as learning how to use our API

A set of assumptions such as:

Familiar with Go

Comfortable following a set of command-line instructions

Has a laptop running either Windows or macOS and has downloaded the SDK

As you write, always favor your reader. It is a good idea to let them know up front what assumptions you’re making, and provide links to resources where they can learn more. Within the document itself, it is also good practice to define both scope and non-scope, e.g.:

This document describes in detail the API for the Company Ignition System. It does not describe the underlying architecture, which is covered in the Company Ignition Architecture Guide.

Writing Principles
Defining the scope and non-scope is helpful for the reader but is also useful to you as a writer since it helps you to stay on topic. Knowing who your audience is can also assist with some of your other decisions. For example, when introducing a concept or technical jargon, it is useful to know whether your audience is likely to be familiar with it already.

If you’re using terminology that may be unfamiliar to your readers, you can link to an authoritative online source or provide a short definition. If you need to include a large number of technical terms, supply and/or link to a glossary.

Make sure you use terms consistently. If you change the name of a variable partway through a function, your code won’t compile. If you rename something partway through a document, it likewise won’t compile in your reader’s head. For example, if you call something “Protocol Buffers,” don’t switch to using “Protobufs” partway through unless you are confident that the reader will know that the terms are interchangeable. If you want to use a shortened form, spell it out the first time and put the shortened form in parentheses afterwards—e.g., Protocol Buffers (Protobufs for short). Thereafter you can use the shortened form.

This applies equally to acronyms. When mentioning an unfamiliar acronym for the first time, spell it out in full and put the acronym in parentheses. Acronyms that are already familiar to your audience are an exception. For a junior programmer you probably don’t need to explain RAM, ROM, HTML or CSS, but you might want to spell out Layer Two Tunnelling Protocol (L2TP).

Our industry is overly fond of Three Letter Acronyms (TLAs), so watch out for their overuse in your writing. If your document starts to look like a bowl of alphabet soup, go back and write some of the abbreviations in full.

Technical readers generally like lists. There are two main types—numbered and bulleted. This is an example of the latter:

Reordering the items in a bulleted list does not change the meaning.

Reordering the items on a numbered list does change the meaning.

For a set of instructions where the chronology has a bearing on the meaning, use a numbered list, such as:

Click on the Settings button in the top-right corner.

Click on the Identities tab.

Review the list of email addresses you have identities configured for. If any are missing, click the + sign in the Identities column and create a new one.

Watch out for consistency with how you punctuate your lists. With bullet points, it’s best to avoid unnecessary punctuation, like periods, unless each listing is a full sentence (or multiple sentences). Apply the same approach throughout and end each point the same way—with or without a period, but don’t mix and match.

Get into the habit of using a dictionary or thesaurus, either in book form or online. If you are not sure what a word means, or simply want to express yourself in a different way, look it up. A book on grammar, such as Lynne Truss’ classic Eats, Shoots and Leaves, can also be helpful.

Technical writing is not the place to show off your extensive vocabulary. As an industry, we love using complicated words. We hate calling a spade a spade when we can call it an “earth-inverting horticultural implement for the purposes of digging (EIHIPD).” Clear writing requires you to rein in this tendency. Avoid using words that obfuscate meaning.

Like well-written code, a clear sentence comes from clear thinking. In my favorite book on writing, William Zinsser’s On Writing Well, he says that, “The secret of good writing is to strip your sentence to its cleanest components.” Just as with code, your goal should be to write the cleanest, clearest sentences you can.

To this end, prune your adverbs—they are mostly unnecessary. The same applies to adjectives. If a sentence starts to feel overly long, you are probably trying to shoehorn too many thoughts into it. Can the sentence be split into two or more sentences, or turned into a list? The vast majority of sentences in technical writing should be in the active voice (e.g., “he sent the email”), rather than the passive voice (e.g., “the email was sent”).

Writing is first and foremost a visual medium. Your reader will see what your document looks like before they read a single word. Focus each paragraph on a single topic. Aim to keep your paragraphs short; long paragraphs can be intimidating. As a rule of thumb, three or four sentences is about right, but vary the length so every paragraph doesn’t wind up looking the same. A well judged and attractive illustration can also make a difference in terms of how likely a reader is to engage with your content.

I have a tendency to overuse qualifiers but William Zinsser notes that, “Good writing is lean and confident.” Instead of saying, “Some people have suggested that Kubernetes might be considered to be overly complex in certain circumstances,” simply state, “Kubernetes is complicated.”

Write your documentation with accessibility and inclusivity in mind. The Google developer documentation style guide provides helpful, though not exhaustive, guidelines for accessibility and inclusive language.

Revise
If my experience as an editor is anything to go by, writers get very attached to their first draft and struggle to imagine that it isn’t perfect. But most writers, including professional writers, don’t initially say what they want to, or say it as well as they could. What this means is that revising is the very essence of writing well.

Get into the habit of reviewing and revising. As you edit your text, look for places where the document doesn’t flow and think about whether the structure works. Don’t be afraid of moving whole sections around or cutting clutter. Watch out for duplication and eliminate it where possible.

As part of your reviewing process, get into the habit of reading your writing aloud. Does it sound like something you’d say?

Once you are happy, get someone else to review it. If you have access to an experienced editor or colleague whose input you value, get them to review it and use their comments as an opportunity to learn and improve.

Finally remember, good writing is akin to good coding—it requires clarity, consistency, and continuous refinement. Revise, seek feedback, and always aim for clean, confident, and well-structured communication. By doing so, you not only enhance your own skills but also contribute to the overall success of your projects and teams.