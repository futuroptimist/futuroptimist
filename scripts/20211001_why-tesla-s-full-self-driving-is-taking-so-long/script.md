# Why Tesla's Full Self Driving is taking so long

> Transcript for video `RDEKyxDIuLQ`

## Script

[NARRATOR]: Many people predict that fully autonomous vehicles are still decades away, while others claim that it's right around the corner.

[NARRATOR]: Tesla has just begun rolling out its Full Self Driving beta to more customers and other companies are also working on self-driving solutions.

[NARRATOR]: In this video I want to talk about the importance of self-driving cars, summarize the current state of self-driving and discuss the near-to-distant future.

[NARRATOR]: I'll try to make this as approachable as possible while also being fairly detailed.

[NARRATOR]: For the purposes of the video, I'm using the terms autonomous, self-driving and driverless interchangeably.

[NARRATOR]: Before we talk specifics, I want to address questions or concerns that someone might have if they haven't given self-driving much thought or if they consider themselves skeptics.

[NARRATOR]: The ultimate goal is a vehicle that is completely self-sufficient. It doesn't need human intervention at all and can make correct decisions with high accuracy.

[NARRATOR]: This is commonly referred to as Level 5 autonomy. We're not quite there yet, as I'll discuss later in the video.

[NARRATOR]: However, once we do reach Level 5 and gain regulatory approval, we can mostly regain the amount of time we spend commuting by car.

[NARRATOR]: According to a 2019 poll, the average U.S. driver spends 35 minutes per day commuting to and from work.

[NARRATOR]: That's roughly 213 hours per year.

[NARRATOR]: The actual amount may vary by individual, but imagine what you could do with another 213 hours per year.

[NARRATOR]: If you could fully delegate driving to your vehicle, you could hypothetically spend that commute time napping, playing a game, getting extra work done, or just relaxing.

[NARRATOR]: Additionally, the price of rideshare would go down dramatically because the driver would be removed from the equation.

[NARRATOR]: Imagine not having to pay $100 for a ride to the airport.

[NARRATOR]: Most people barely use their cars outside of commute and errands, so they could lend their car to a network of rideshare vehicles and earn extra money on the side.

[NARRATOR]: In fact, car ownership wouldn't be nearly as essential if you could cheaply and easily hail a driverless rideshare vehicle.

[NARRATOR]: Finally, consider all the space in cities dedicated to parking.

[NARRATOR]: If a driverless car could drop you off and pick you up as needed, the need for parking could be reduced substantially.

[NARRATOR]: What was previously a parking lot could become a park or additional housing.

[NARRATOR]: If you're still not convinced about this potential driverless future, let me know in the comments and we'll have a dialogue.

[NARRATOR]: Before we go any further, let's talk about the most commonly used classification system for self-driving cars, defined by a group known as SAE International.

[NARRATOR]: This system places self-driving cars in one of six levels, numbered zero through five.

[NARRATOR]: Level 0 implies no autonomous system whatsoever, while Level 5 requires no human intervention at all.

[NARRATOR]: Most modern vehicles at the time of this video are somewhere between Level 1 and Level 2.

[NARRATOR]: More specifically, popular solutions like Tesla's Autopilot and Comma.ai's openpilot are examples of Level 2 autonomy.

[NARRATOR]: Things get a little complicated after Level 2 though.

[NARRATOR]: Level 2 is considered hands off, Level 3 is eyes off, Level 4 is mind off, and Level 5 is considered steering wheel optional.

[NARRATOR]: In my opinion, getting past Level 2 will be an enormous regulatory hurdle and in practice we'll probably be on Level 2 for a while until we're finally at Level 5.

[NARRATOR]: I'll talk about my reasoning for this later, but first let's look at where the various companies are right now.

[NARRATOR]: Full disclosure, my current vehicle is a Tesla Model 3 and my future vehicles will likely be Teslas as well.

[NARRATOR]: I am very tempted to get a Cybertruck once those are available, assuming I can afford one when that time comes.

[NARRATOR]: I know they're an acquired taste, but as a sci-fi nerd this is my ideal vehicle.

[NARRATOR]: I say all this because while I strive to be as objective as possible, this video is heavily weighted toward Teslas and is probably influenced by my confirmation bias.

[NARRATOR]: With that out of the way, let's talk about the current state of the industry, starting with non-Teslas.

[NARRATOR]: Of course, all the old school car companies are in various states of electrifying and automating their fleets.

[NARRATOR]: There are many cars with autosteer or adaptive cruise control, which meet the SAE standard for Level 2 automation.

[NARRATOR]: This includes Tesla's Autopilot software, which comes standard when you purchase a Tesla.

[NARRATOR]: At the risk of sounding biased, it's probably the best solution out there. Don't at me.

[NARRATOR]: Probably the most promising non-Tesla contender is Waymo.

[NARRATOR]: Waymo is owned by Google and is taking a radically different approach than Tesla in its path to Level 5.

[NARRATOR]: Waymo is attempting to perfect full self-driving one locale at a time, starting with Phoenix, Arizona, where you can request a fully autonomous rideshare vehicle right now and experience a completely driverless ride.

[NARRATOR]: The idea is to expand one locale at a time, starting with the least difficult scenario and progressing horizontally in difficulty.

[NARRATOR]: Tesla, on the other hand, is expanding vertically using a strategy I'll describe in the next section.

[NARRATOR]: But before we do that, I'll go through some honorable mentions.

[NARRATOR]: First there's Comma.ai, which provides a kit that you can attach to existing modern vehicles, thereby retrofitting them to support Level 2 autonomy.

[NARRATOR]: Comma.ai is proudly a Level 2 solution only and its openpilot system is fully open-sourced.

[NARRATOR]: There are also a few other notable solutions in the works, including San Francisco-based Cruise, Intel's Mobileye, and various Chinese companies including AutoX, Pony.ai, and WeRide.

[NARRATOR]: It's worth noting that while a few companies claim to be SAE Level 3 or higher, I'm highly skeptical because I don't think that'll pass regulatory scrutiny in the near term, especially in the United States.

[NARRATOR]: Now that we've talked about some non-Tesla cars, let's discuss what most of you are probably interested in, Tesla's Full Self Driving capability, which is slowly rolling out to FSD owners and subscribers who have a certain minimum Safety Score.

[NARRATOR]: This Safety Score and its underlying formula are documented in detail on the Tesla website.

[NARRATOR]: It includes your number of forward collision warnings, hard braking, aggressive turning, whether you tailgate other cars, and forced disengagements.

[NARRATOR]: The formula for this score will evolve over time to more closely predict your probability of getting into an accident.

[NARRATOR]: This gating mechanism for the FSD beta ensures that only the safest drivers have access to the system while it's still in its infancy.

[NARRATOR]: Access to FSD Beta will be rolled out at around 1,000 cars per day, starting with the highest score of 100 and proceeding in descending order.

[NARRATOR]: Elon says that the private FSD beta has been progressing for about a year with two thousand participants and zero accidents.

[NARRATOR]: There are still lots of edge cases to discover and fix, which is why FSD participants must be incredibly vigilant and ready to take over at any time.

[NARRATOR]: Those edge cases are an extremely hard challenge because there are many rare scenarios that might be obvious for a human to navigate but prove especially challenging for a training model to handle.

[NARRATOR]: With our current understanding of machine learning models, such a scenario usually needs thousands of examples to train on, which is where Tesla's simulation stack comes in.

[NARRATOR]: The simulation replays certain scenarios, both with human-prepared and procedurally generated environments, so even the rarest edge cases have adequate representation in the training model.

[NARRATOR]: The path from where we are now to full Level 5 autonomy will involve the march of nines.

[NARRATOR]: When talking about reliability or high availability, having a 100% reliable service is virtually impossible, so engineers commit to a certain number of nines.

[NARRATOR]: One nine represents 90% reliability, two nines is 99%, three nines is 99.9% and so on.

[NARRATOR]: The higher the criticality of your product or service, the more nines you need.

[NARRATOR]: As the training model improves and more edge cases are discovered, we'll see continuous improvement in reliability, which will show up for the user as fewer disengagements.

[NARRATOR]: Tesla collects an incredible amount of data from its cars, and providing this data to regulators and convincing them of the reliability will be essential to achieving Level 5.

[NARRATOR]: Until that time is reached, those of us driving Teslas must be vigilant in making sure we're paying attention to the road.

[NARRATOR]: We should treat the self-driving side of our car as a student driver and accept that it'll likely make mistakes more frequently than we do, at least for now.

[NARRATOR]: Correct me if I'm wrong, but I think we'll be stuck at Level 2 for a while and then suddenly, one day legislation will pass and we'll be at Level 5.

[NARRATOR]: Then we'll finally be able to legally fall asleep at the wheel on our way to work.

[NARRATOR]: One thing to keep in mind is that each additional nine of reliability results in a tenfold reduction in errors or unhandled edge cases.

[NARRATOR]: Our Level 2 driving experience will gradually start resembling the Level 5 experience, and from what I've seen in the Full Self Driving beta so far, that will probably start happening right around the corner.

[NARRATOR]: Make sure you pay attention at all times until we're officially at Level 5.

[NARRATOR]: Your life or someone else's life may depend on it.

[NARRATOR]: Let's make this rollout nice and smooth and leave a good lasting impression on the general public and regulators.

[NARRATOR]: That's it for this video. I'd greatly appreciate if you smashed that subscribe button and let me know in the comments if you have any criticisms or suggestions for future videos.

[NARRATOR]: I'll see you in the next one.

