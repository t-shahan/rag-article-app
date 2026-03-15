import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# Simulated article data — in a real app these would come from a database or API
ARTICLES = [
    {
        "id": "article_001",
        "title": "The Rise of Renewable Energy",
        "content": (
            "Renewable energy sources such as solar, wind, and hydroelectric power are transforming "
            "the global energy landscape. Over the past decade, the cost of solar panels has dropped "
            "by over 90%, making clean energy accessible to more countries than ever before. "
            "Governments worldwide are setting ambitious targets to phase out fossil fuels and reach "
            "net-zero carbon emissions by 2050. Wind farms, both onshore and offshore, are expanding "
            "rapidly, with offshore installations taking advantage of stronger, more consistent winds. "
            "Energy storage technology, particularly lithium-ion batteries, is solving the intermittency "
            "problem that once limited renewables. The transition to clean energy is not just an "
            "environmental imperative — it is increasingly an economic one."
        ),
    },
    {
        "id": "article_002",
        "title": "How Large Language Models Work",
        "content": (
            "Large language models (LLMs) are neural networks trained on vast amounts of text data. "
            "They learn to predict the next token in a sequence, which — at scale — produces systems "
            "capable of reasoning, summarization, and code generation. The transformer architecture, "
            "introduced in the 2017 paper 'Attention Is All You Need', is the foundation of modern LLMs. "
            "Attention mechanisms allow the model to weigh the relevance of every word in a sentence "
            "relative to every other word, capturing long-range dependencies that earlier models missed. "
            "Training requires massive compute clusters running for weeks or months. Fine-tuning and "
            "reinforcement learning from human feedback (RLHF) align the raw model to be helpful, "
            "harmless, and honest. LLMs like GPT-4 and Claude are now embedded in products used by "
            "hundreds of millions of people daily."
        ),
    },
    {
        "id": "article_003",
        "title": "The History of the Internet",
        "content": (
            "The internet began as ARPANET, a US Department of Defense project in the late 1960s designed "
            "to create a decentralized communication network that could survive a nuclear attack. Early "
            "adoption was limited to universities and research institutions. The invention of the World "
            "Wide Web by Tim Berners-Lee in 1989 democratized access, introducing hyperlinks and browsers "
            "that made navigation intuitive. The 1990s saw explosive commercial growth, culminating in the "
            "dot-com bubble and bust. Broadband replaced dial-up in the 2000s, enabling video streaming "
            "and social media. Mobile internet, driven by smartphones, made connectivity ubiquitous. "
            "Today, over five billion people are online, and the internet underpins nearly every sector "
            "of the global economy."
        ),
    },
    {
        "id": "article_004",
        "title": "Advances in CRISPR Gene Editing",
        "content": (
            "CRISPR-Cas9 is a molecular tool that allows scientists to edit DNA with unprecedented "
            "precision. Derived from a bacterial immune system, CRISPR uses a guide RNA to direct the "
            "Cas9 enzyme to a specific location in the genome, where it makes a targeted cut. Researchers "
            "can then disable a gene or insert new genetic material. Since its adaptation for human cells "
            "in 2012, CRISPR has accelerated research into genetic diseases, cancer therapies, and crop "
            "improvement. Clinical trials are underway for sickle cell disease and beta-thalassemia, with "
            "early results showing patients achieving functional cures. Ethical debates around germline "
            "editing — changes that would be inherited by future generations — remain active and unresolved. "
            "CRISPR represents both enormous promise and significant responsibility."
        ),
    },
    {
        "id": "article_005",
        "title": "The Economics of Remote Work",
        "content": (
            "The COVID-19 pandemic forced a global experiment in remote work, accelerating a shift that "
            "was already underway. Knowledge workers discovered that many tasks previously assumed to "
            "require in-person presence could be done effectively from home. Companies reported mixed "
            "results: some saw productivity gains, others struggled with collaboration and culture. "
            "Real estate markets shifted dramatically as workers relocated from expensive cities to "
            "lower-cost regions, enabled by geographic flexibility. Employers began competing for talent "
            "on a global scale, compressing wages in high-cost markets while raising them elsewhere. "
            "Hybrid work — a mix of in-office and remote days — emerged as the dominant model for large "
            "organizations. The long-term economic effects, from commercial real estate to urban tax bases, "
            "are still unfolding."
        ),
    },
    {
        "id": "article_006",
        "title": "The Science of Climate Change",
        "content": (
            "Climate change refers to long-term shifts in global temperatures and weather patterns. While "
            "natural factors have always influenced climate, since the Industrial Revolution human activities "
            "have become the dominant driver. Burning fossil fuels releases carbon dioxide and methane, "
            "greenhouse gases that trap heat in the atmosphere. The global average temperature has risen "
            "approximately 1.2 degrees Celsius since pre-industrial times, with the last decade being the "
            "warmest on record.\n\n"
            "The consequences are wide-ranging. Sea levels are rising as glaciers and polar ice sheets melt, "
            "threatening coastal cities and island nations. Extreme weather events — hurricanes, droughts, "
            "wildfires, and floods — are becoming more frequent and intense. Ocean acidification, caused by "
            "oceans absorbing excess CO2, is disrupting marine ecosystems and threatening coral reefs.\n\n"
            "The Intergovernmental Panel on Climate Change (IPCC) warns that limiting warming to 1.5 degrees "
            "Celsius above pre-industrial levels requires cutting global emissions roughly in half by 2030 "
            "and reaching net zero by 2050. Achieving this demands a rapid transition away from fossil fuels, "
            "widespread adoption of renewable energy, changes in land use, and significant investment in "
            "carbon capture technologies. Climate change is not a future problem — its effects are already "
            "being felt by communities around the world."
        ),
    },
    {
        "id": "article_007",
        "title": "Quantum Computing Explained",
        "content": (
            "Quantum computing harnesses the principles of quantum mechanics to process information in "
            "fundamentally different ways than classical computers. Where classical bits represent either "
            "0 or 1, quantum bits — called qubits — can exist in a superposition of both states simultaneously. "
            "This property, combined with entanglement and interference, allows quantum computers to explore "
            "many possible solutions to a problem at once.\n\n"
            "The potential applications are transformative. Quantum computers could break current encryption "
            "standards, simulate molecular behavior for drug discovery, optimize complex logistics networks, "
            "and accelerate machine learning. Google claimed 'quantum supremacy' in 2019 when its Sycamore "
            "processor performed a calculation in 200 seconds that would take a classical supercomputer "
            "thousands of years.\n\n"
            "However, quantum computing faces enormous engineering challenges. Qubits are extremely fragile — "
            "any interaction with the environment causes 'decoherence,' destroying the quantum state. "
            "Current systems require cooling to near absolute zero and are prone to errors. Error correction "
            "remains an active area of research. Most experts believe fault-tolerant, general-purpose quantum "
            "computers are still a decade or more away. In the meantime, hybrid classical-quantum algorithms "
            "are being developed to extract value from today's noisy intermediate-scale quantum (NISQ) devices."
        ),
    },
    {
        "id": "article_008",
        "title": "The Human Microbiome",
        "content": (
            "The human body hosts trillions of microorganisms — bacteria, viruses, fungi, and archaea — "
            "collectively known as the microbiome. The gut microbiome alone contains roughly 100 trillion "
            "microbial cells, outnumbering human cells. Far from being mere passengers, these microbes play "
            "essential roles in digestion, immune function, vitamin synthesis, and even mood regulation.\n\n"
            "Research over the past two decades has linked microbiome imbalances — called dysbiosis — to a "
            "wide range of conditions including inflammatory bowel disease, obesity, type 2 diabetes, "
            "allergies, and depression. The gut-brain axis, a bidirectional communication pathway between "
            "the gut and the central nervous system, has emerged as a key area of study. Certain gut "
            "bacteria produce neurotransmitters like serotonin, suggesting the microbiome may influence "
            "mental health.\n\n"
            "Diet is the most powerful tool for shaping the microbiome. High-fiber diets rich in fruits, "
            "vegetables, and fermented foods promote microbial diversity, which is associated with better "
            "health outcomes. Antibiotics, while life-saving, can devastate microbial communities and "
            "increase susceptibility to pathogens. Fecal microbiota transplants — transferring stool from "
            "a healthy donor to a sick recipient — have shown remarkable effectiveness against recurrent "
            "C. difficile infections and are being studied for other conditions. The microbiome represents "
            "one of the most exciting frontiers in modern medicine."
        ),
    },
    {
        "id": "article_009",
        "title": "Blockchain and Cryptocurrency",
        "content": (
            "A blockchain is a distributed ledger — a record of transactions maintained simultaneously "
            "across thousands of computers with no central authority. Each block of transactions is "
            "cryptographically linked to the previous one, making the chain tamper-evident. Bitcoin, "
            "launched in 2009 by the pseudonymous Satoshi Nakamoto, was the first application of "
            "blockchain technology, creating a decentralized digital currency that enables peer-to-peer "
            "payments without banks.\n\n"
            "Ethereum expanded the concept with smart contracts — self-executing programs stored on the "
            "blockchain that automatically enforce the terms of an agreement. This enabled decentralized "
            "finance (DeFi), non-fungible tokens (NFTs), and decentralized autonomous organizations (DAOs). "
            "The total market capitalization of cryptocurrencies peaked above $3 trillion in 2021 before "
            "a sharp correction exposed the sector's volatility and regulatory risks.\n\n"
            "Proponents argue blockchain can democratize finance, reduce fraud, and eliminate costly "
            "intermediaries. Critics point to the enormous energy consumption of proof-of-work consensus "
            "mechanisms, the prevalence of scams, and the lack of consumer protections. Governments "
            "worldwide are developing regulatory frameworks, and several central banks are exploring "
            "central bank digital currencies (CBDCs). Whether blockchain delivers on its transformative "
            "promise or remains a niche technology remains actively debated."
        ),
    },
    {
        "id": "article_010",
        "title": "The New Space Race",
        "content": (
            "The original space race between the United States and Soviet Union during the Cold War "
            "culminated in the Apollo 11 moon landing in July 1969. After the fall of the Soviet Union, "
            "space exploration shifted to international cooperation, exemplified by the International "
            "Space Station — a joint project involving NASA, Roscosmos, ESA, JAXA, and CSA that has "
            "been continuously inhabited since 2000.\n\n"
            "The 21st century has brought a new era of space exploration driven by private companies. "
            "SpaceX, founded by Elon Musk in 2002, disrupted the industry by developing reusable "
            "rockets, dramatically reducing launch costs. Blue Origin, founded by Jeff Bezos, and "
            "Virgin Galactic are pursuing space tourism. NASA's Artemis program aims to return humans "
            "to the Moon by the late 2020s as a stepping stone to Mars.\n\n"
            "Beyond national prestige, the new space race is driven by economic opportunity. Satellite "
            "internet constellations like SpaceX's Starlink aim to provide global broadband coverage. "
            "Asteroid mining could theoretically unlock vast mineral resources. Mars colonization, once "
            "science fiction, is now the stated long-term goal of multiple organizations. China and India "
            "have also significantly expanded their space programs, and over 70 countries now have some "
            "form of space agency. The next decades promise to be among the most consequential in the "
            "history of space exploration."
        ),
    },
    {
        "id": "article_011",
        "title": "Artificial Intelligence in Healthcare",
        "content": (
            "Artificial intelligence is transforming medicine at every level, from drug discovery to "
            "diagnosis to patient care. Machine learning models trained on millions of medical images "
            "can detect cancers, diabetic retinopathy, and other conditions with accuracy rivaling or "
            "exceeding expert clinicians. Google's DeepMind developed AlphaFold, which solved the "
            "50-year-old protein folding problem — a breakthrough with enormous implications for "
            "understanding disease and designing new drugs.\n\n"
            "In clinical settings, AI-powered tools assist radiologists in reading scans, flag "
            "deteriorating patients in ICUs before vital signs visibly change, and help pathologists "
            "identify cancerous cells in tissue samples. Natural language processing extracts insights "
            "from unstructured clinical notes, making electronic health records more useful. AI is also "
            "accelerating drug discovery by predicting how candidate molecules will interact with "
            "biological targets, compressing a process that once took years into weeks.\n\n"
            "Significant challenges remain. AI models trained on biased datasets can perpetuate health "
            "disparities. Regulatory approval for AI medical devices is complex and evolving. "
            "Clinicians must trust and understand AI recommendations, which requires explainability "
            "that many deep learning models currently lack. Patient privacy is a central concern when "
            "training models on sensitive health data. Despite these hurdles, AI is widely expected to "
            "become an indispensable tool in 21st-century medicine."
        ),
    },
    {
        "id": "article_012",
        "title": "The Psychology of Social Media",
        "content": (
            "Social media platforms have fundamentally altered how billions of people communicate, "
            "consume information, and perceive themselves and others. Designed around variable reward "
            "schedules — the same psychological mechanism that makes slot machines addictive — platforms "
            "like Instagram, TikTok, and X (formerly Twitter) optimize for engagement above all else, "
            "which often means amplifying outrage, anxiety, and social comparison.\n\n"
            "Research has linked heavy social media use to increased rates of depression and anxiety, "
            "particularly among adolescent girls. The constant exposure to curated highlight reels of "
            "others' lives distorts social comparison, while cyberbullying has become a serious public "
            "health concern. The spread of misinformation is another documented harm — false content "
            "spreads faster than true content on social platforms, with significant consequences for "
            "public health and democratic discourse.\n\n"
            "The picture is not uniformly negative. Social media enables connection across geography, "
            "gives voice to marginalized communities, supports social movements, and provides genuine "
            "community for isolated individuals. The mental health effects appear to depend heavily on "
            "how platforms are used — passive scrolling is more harmful than active engagement. "
            "Policymakers, researchers, and platforms themselves are grappling with how to preserve "
            "the benefits of social media while mitigating its documented harms, including proposals "
            "for age verification, algorithm transparency, and data portability."
        ),
    },
    {
        "id": "article_013",
        "title": "Nuclear Energy: Risks and Potential",
        "content": (
            "Nuclear power generates electricity by splitting heavy atoms — typically uranium-235 — in "
            "a controlled chain reaction that produces heat to drive steam turbines. It is one of the "
            "lowest-carbon sources of electricity available, producing lifecycle emissions comparable "
            "to wind power. Today, nuclear provides about 10% of global electricity, with France "
            "generating nearly 70% of its power from nuclear plants.\n\n"
            "The accidents at Three Mile Island (1979), Chernobyl (1986), and Fukushima (2011) shaped "
            "public perception of nuclear power, triggering widespread shutdowns in many countries. "
            "Yet statistical analysis shows nuclear has among the lowest deaths-per-terawatt-hour of "
            "any energy source — far fewer than coal, oil, or even rooftop solar. The primary ongoing "
            "challenges are the cost and time required to build new plants, and the management of "
            "long-lived radioactive waste.\n\n"
            "A new generation of nuclear technology is emerging. Small modular reactors (SMRs) promise "
            "to be cheaper and faster to build than conventional plants. Advanced reactor designs use "
            "thorium fuel or molten salt coolants to reduce waste and improve safety. Nuclear fusion — "
            "which powers the sun — has long been the holy grail of clean energy: in 2022, the National "
            "Ignition Facility achieved fusion ignition for the first time, producing more energy from "
            "fusion than was delivered by the laser. Commercial fusion power remains years away, but "
            "the milestone renewed excitement about its potential."
        ),
    },
    {
        "id": "article_014",
        "title": "The History and Science of Vaccines",
        "content": (
            "Vaccination is one of the most effective public health interventions in history. Edward "
            "Jenner pioneered the concept in 1796 when he demonstrated that inoculation with cowpox "
            "protected against smallpox. Louis Pasteur extended the principle in the 19th century, "
            "developing vaccines for cholera, anthrax, and rabies. Smallpox was declared eradicated "
            "in 1980 — the only human disease ever eliminated through vaccination — and polio has been "
            "eliminated from all but a handful of countries.\n\n"
            "Vaccines work by training the immune system to recognize and fight a pathogen without "
            "causing the disease itself. Traditional vaccines use weakened or killed pathogens, or "
            "pieces of them, to trigger an immune response. The COVID-19 pandemic accelerated the "
            "deployment of mRNA vaccine technology, which instead instructs cells to produce a "
            "harmless protein from the pathogen, prompting an immune response. mRNA vaccines can be "
            "designed and manufactured faster than conventional vaccines, opening new possibilities "
            "for rapid response to emerging diseases.\n\n"
            "Vaccine hesitancy — reluctance or refusal to vaccinate despite availability — has emerged "
            "as a significant public health challenge. Fueled by misinformation online, hesitancy has "
            "allowed diseases like measles to resurge in communities with previously high vaccination "
            "rates. Herd immunity, which protects those who cannot be vaccinated, requires high "
            "community coverage — typically 90–95% for measles. Building and maintaining public trust "
            "in vaccines is as important as the science behind them."
        ),
    },
    {
        "id": "article_015",
        "title": "Autonomous Vehicles",
        "content": (
            "Autonomous vehicles (AVs) use a combination of sensors — cameras, lidar, radar, and "
            "ultrasonic detectors — along with machine learning and detailed maps to navigate roads "
            "without human input. The Society of Automotive Engineers defines six levels of automation "
            "ranging from Level 0 (no automation) to Level 5 (full automation under all conditions). "
            "Most consumer vehicles today are at Level 2, offering features like adaptive cruise "
            "control and lane centering that still require driver supervision.\n\n"
            "Waymo, a subsidiary of Alphabet, operates fully driverless robotaxi services in select "
            "U.S. cities. Tesla's Autopilot and Full Self-Driving systems are Level 2, despite their "
            "names suggesting otherwise. The gap between current capabilities and Level 5 remains "
            "significant — edge cases like unusual weather, construction zones, and unpredictable "
            "pedestrian behavior remain challenging for AI systems.\n\n"
            "The potential benefits of AVs are substantial: an estimated 94% of serious crashes in "
            "the U.S. involve human error, suggesting AVs could save tens of thousands of lives "
            "annually. Autonomous vehicles could also improve mobility for elderly and disabled "
            "populations and reduce traffic congestion through coordinated driving. However, "
            "questions around liability, cybersecurity, job displacement of professional drivers, "
            "and the ethical programming of collision-avoidance decisions remain unresolved and "
            "contentious."
        ),
    },
    {
        "id": "article_016",
        "title": "Antibiotic Resistance",
        "content": (
            "Antibiotics are among the most important discoveries in medical history. Since Alexander "
            "Fleming discovered penicillin in 1928, antibiotics have saved hundreds of millions of "
            "lives by defeating bacterial infections that were once death sentences. However, bacteria "
            "evolve rapidly, and the overuse and misuse of antibiotics has accelerated the spread of "
            "resistant strains. Antibiotic resistance is now one of the greatest threats to global "
            "health.\n\n"
            "When bacteria are exposed to antibiotics, susceptible strains die while resistant ones "
            "survive and reproduce — a process of natural selection that antibiotic overuse actively "
            "drives. Resistance genes can also spread horizontally between bacteria of different "
            "species. The World Health Organization estimates that drug-resistant infections currently "
            "kill over a million people annually, a number projected to rise sharply by 2050 without "
            "intervention.\n\n"
            "The problem is compounded by a dry pipeline of new antibiotics: developing new drugs is "
            "expensive and the financial returns are limited, since new antibiotics are reserved as "
            "treatments of last resort. Addressing antibiotic resistance requires reducing unnecessary "
            "prescriptions in humans, curtailing the use of antibiotics in livestock agriculture, "
            "improving global surveillance of resistant strains, and creating economic incentives for "
            "pharmaceutical companies to invest in new antimicrobials. Bacteriophage therapy — using "
            "viruses that infect bacteria — is one promising alternative being explored."
        ),
    },
    {
        "id": "article_017",
        "title": "Brain-Computer Interfaces",
        "content": (
            "Brain-computer interfaces (BCIs) are devices that establish a direct communication pathway "
            "between the brain and an external computer. They work by recording electrical signals from "
            "neurons and translating them into commands that can control software, prosthetics, or other "
            "devices. BCIs have existed in research settings for decades, primarily helping patients with "
            "paralysis communicate or control robotic limbs.\n\n"
            "Neuralink, founded by Elon Musk, aims to implant tiny electrode arrays directly into the "
            "brain to achieve high-bandwidth communication. In 2024, the company announced its first "
            "human patient was able to control a computer cursor with thought alone. Non-invasive BCIs "
            "using electroencephalography (EEG) are already commercially available for applications "
            "ranging from concentration training to gaming, though their bandwidth is far lower than "
            "implanted devices.\n\n"
            "The potential applications of advanced BCIs are extraordinary: restoring speech and "
            "movement to paralyzed patients, treating neurological disorders like depression and "
            "epilepsy, and eventually augmenting human cognition. The ethical questions are equally "
            "profound. Who owns the neural data generated by a BCI? Could BCIs be used for "
            "surveillance or coercion? What are the implications of a world where cognitive "
            "enhancement is available to the wealthy but not others? BCIs sit at the frontier of "
            "neuroscience, engineering, and bioethics."
        ),
    },
    {
        "id": "article_018",
        "title": "The Global Water Crisis",
        "content": (
            "Fresh water covers less than 3% of Earth's surface, and most of it is locked in glaciers "
            "and ice caps. Yet demand for fresh water from agriculture, industry, and growing urban "
            "populations is pushing many regions to the brink of scarcity. The United Nations estimates "
            "that over two billion people currently live in water-stressed countries, and that by 2050 "
            "global water demand will increase by up to 30%.\n\n"
            "Agriculture accounts for approximately 70% of global fresh water withdrawals, primarily "
            "for irrigation. Inefficient flood irrigation wastes enormous quantities of water, but "
            "transitioning to drip irrigation and other precision techniques requires investment many "
            "farmers cannot afford. Groundwater aquifers — which supply drinking water and irrigation "
            "to billions — are being depleted faster than they can recharge in many regions, from the "
            "Central Valley of California to the North China Plain to the Arabian Peninsula.\n\n"
            "Climate change is worsening the crisis by disrupting precipitation patterns, accelerating "
            "glacier melt, and intensifying droughts. Water stress is already a source of conflict "
            "in regions like the Nile Basin, the Jordan River, and the Mekong River. Solutions include "
            "desalination, water recycling, improved irrigation efficiency, and international water "
            "sharing agreements. Water, once taken for granted in many parts of the world, is "
            "increasingly recognized as a strategic resource."
        ),
    },
    {
        "id": "article_019",
        "title": "Dark Matter and Dark Energy",
        "content": (
            "Ordinary matter — everything made of atoms, from stars to planets to people — accounts for "
            "only about 5% of the universe's total energy content. The remaining 95% consists of two "
            "mysterious components: dark matter (roughly 27%) and dark energy (roughly 68%). Neither "
            "has been directly detected, yet their existence is inferred from their gravitational effects "
            "on ordinary matter and light.\n\n"
            "Dark matter was first proposed to explain why galaxies rotate the way they do. The stars "
            "at the outer edges of galaxies move faster than they should given the visible mass — "
            "something unseen must be providing additional gravitational pull. Gravitational lensing, "
            "where massive objects bend light from objects behind them, also reveals large quantities "
            "of mass that cannot be accounted for by visible matter. The leading candidates for dark "
            "matter are weakly interacting massive particles (WIMPs) and axions, but decades of "
            "experiments have not yet detected them directly.\n\n"
            "Dark energy is even more mysterious. In 1998, observations of distant supernovae revealed "
            "that the expansion of the universe is accelerating — something is counteracting gravity "
            "on the largest scales. This repulsive force, termed dark energy, is often associated with "
            "Einstein's cosmological constant. The nature of dark energy remains one of the deepest "
            "unsolved problems in physics, with profound implications for the ultimate fate of the "
            "universe."
        ),
    },
    {
        "id": "article_020",
        "title": "Vertical Farming and the Future of Food",
        "content": (
            "Vertical farming grows crops in stacked indoor layers using artificial lighting, controlled "
            "climate, and often hydroponic or aeroponic systems that deliver nutrients directly to plant "
            "roots without soil. Proponents argue it could revolutionize food production by enabling "
            "year-round harvests regardless of climate, reducing water usage by up to 95% compared to "
            "conventional farming, and locating food production close to urban consumers, cutting "
            "transportation emissions.\n\n"
            "The technology has advanced rapidly. LED lighting has become efficient enough to make "
            "artificial illumination economically viable for many crops. Automated systems manage "
            "temperature, humidity, CO2 levels, and nutrient delivery with precision. Companies like "
            "AeroFarms, Plenty, and Bowery Farming have built large commercial facilities and secured "
            "significant investment. Leafy greens, herbs, strawberries, and tomatoes are currently "
            "the most economically viable crops for vertical farming.\n\n"
            "Significant challenges remain. Energy consumption is the primary limitation — vertical "
            "farms rely entirely on artificial light, making them expensive to operate and carbon-"
            "intensive unless powered by renewables. Staple crops like wheat, corn, and rice that "
            "require large volumes and low prices are currently not economically viable indoors. "
            "Critics argue that investment in vertical farming might be better directed toward "
            "improving conventional farming efficiency. Nevertheless, as energy costs fall and "
            "climate pressures on conventional agriculture mount, vertical farming is likely to "
            "play a growing role in the global food system."
        ),
    },
    {
        "id": "article_021",
        "title": "The History of Cryptography",
        "content": (
            "Cryptography — the science of secret communication — has been practiced for thousands of "
            "years. The Caesar cipher, used by Julius Caesar to protect military messages, simply "
            "shifted letters by a fixed number in the alphabet. The Vigenère cipher, developed in "
            "the 16th century, used a keyword to vary the shift, making it far harder to break. For "
            "centuries, cryptography was primarily a tool of governments and militaries.\n\n"
            "World War II marked a turning point. Nazi Germany's Enigma machine used mechanical "
            "rotors to create a cipher with billions of possible configurations. The work of Alan "
            "Turing and his colleagues at Bletchley Park to crack Enigma is considered one of the "
            "most consequential achievements of the war, shortening the conflict by an estimated "
            "two years. The effort also laid the groundwork for modern computing.\n\n"
            "The digital age transformed cryptography from a government monopoly into a public tool. "
            "In 1976, Whitfield Diffie and Martin Hellman introduced public-key cryptography — a "
            "system allowing two parties to exchange encrypted messages without ever sharing a "
            "secret key. RSA encryption, developed in 1977, implemented this concept and remains "
            "the backbone of internet security. Today, every time you see HTTPS in a browser, "
            "you are benefiting from this lineage. Quantum computing poses a potential future "
            "threat to RSA and similar systems, driving the development of post-quantum "
            "cryptographic standards."
        ),
    },
    {
        "id": "article_022",
        "title": "Mental Health and the Modern World",
        "content": (
            "Mental health conditions affect roughly one in five adults globally in any given year. "
            "Depression is the leading cause of disability worldwide, followed by anxiety disorders. "
            "Despite this prevalence, mental health has historically received far less research "
            "funding and clinical attention than physical health. Stigma, a shortage of providers, "
            "and inadequate insurance coverage create significant barriers to care in most countries.\n\n"
            "The COVID-19 pandemic triggered a global mental health crisis, with rates of depression "
            "and anxiety surging. Loneliness, economic stress, grief, and disruption to routine took "
            "a severe toll. The crisis also accelerated adoption of teletherapy, expanding access "
            "to mental health services for people in underserved areas. Apps offering guided "
            "meditation, cognitive behavioral therapy exercises, and crisis support have reached "
            "millions of users, though clinical evidence for their effectiveness varies.\n\n"
            "Neuroscience is deepening our understanding of the biological underpinnings of mental "
            "illness. Research has moved beyond the simplistic 'chemical imbalance' theory of "
            "depression toward a more complex picture involving neural circuits, inflammation, "
            "and the gut-brain axis. Psychedelic-assisted therapy, using substances like psilocybin "
            "and MDMA in controlled therapeutic settings, has shown remarkable results in clinical "
            "trials for treatment-resistant depression and PTSD. Regulatory approval for some "
            "psychedelic therapies appears imminent in several countries."
        ),
    },
    {
        "id": "article_023",
        "title": "Ocean Acidification",
        "content": (
            "The world's oceans have absorbed roughly 30% of the carbon dioxide humans have emitted "
            "since the Industrial Revolution. While this has slowed the buildup of CO2 in the "
            "atmosphere, it has come at a cost: when CO2 dissolves in seawater, it forms carbonic "
            "acid, lowering the ocean's pH. Since the Industrial Revolution, average ocean pH has "
            "dropped from 8.2 to 8.1 — a seemingly small change that represents a 26% increase in "
            "acidity, as pH is measured on a logarithmic scale.\n\n"
            "Ocean acidification poses a serious threat to marine life, particularly shell-forming "
            "organisms. Oysters, clams, sea urchins, and corals build their shells and skeletons "
            "from calcium carbonate, which dissolves more readily in acidic water. Coral reefs — "
            "which support roughly 25% of all marine species despite covering less than 1% of the "
            "ocean floor — are already bleaching and dissolving at unprecedented rates. Pteropods, "
            "tiny sea snails at the base of many marine food webs, show shell dissolution in "
            "waters already affected by acidification.\n\n"
            "The impacts ripple through entire ecosystems and into human economies. Fisheries worth "
            "hundreds of billions of dollars depend on healthy marine ecosystems. Shellfish aquaculture "
            "on the U.S. West Coast has already reported losses attributed to more acidic upwelling "
            "waters. Unlike surface-level pollution, ocean acidification cannot be quickly reversed "
            "once set in motion — oceans take thousands of years to naturally return to previous "
            "pH levels. Reducing CO2 emissions remains the only effective long-term solution."
        ),
    },
    {
        "id": "article_024",
        "title": "The Future of Work and Automation",
        "content": (
            "Automation has displaced workers throughout history — the mechanization of agriculture "
            "and the factory assembly line transformed labor markets in the 19th and 20th centuries. "
            "The current wave of automation, driven by robotics and artificial intelligence, is "
            "different in scope: for the first time, cognitive tasks as well as physical ones are "
            "subject to automation. Machine learning systems can now write code, analyze legal "
            "documents, diagnose medical images, and conduct customer service interactions.\n\n"
            "Economists disagree about the net effect. Optimists argue that automation historically "
            "creates more jobs than it destroys by lowering costs, increasing productivity, and "
            "enabling entirely new industries. Pessimists counter that the pace of change this time "
            "is unprecedented and that many workers, particularly those in routine cognitive jobs, "
            "will find it difficult to transition to roles that require creativity, emotional "
            "intelligence, or complex judgment. The distributional effects are a particular concern — "
            "the gains from automation tend to accrue to capital owners and highly skilled workers, "
            "while costs fall on lower-wage workers.\n\n"
            "Policy responses under discussion include investing in education and retraining programs, "
            "strengthening social safety nets, reducing barriers to labor market mobility, and "
            "exploring mechanisms like robot taxes or universal basic income to redistribute "
            "productivity gains. The future of work will be shaped not just by technological "
            "capabilities but by the political choices societies make about how to manage "
            "the transition."
        ),
    },
    {
        "id": "article_025",
        "title": "The Geopolitics of Artificial Intelligence",
        "content": (
            "Artificial intelligence has become a central arena of geopolitical competition. The "
            "United States and China are engaged in a strategic rivalry for AI dominance, recognizing "
            "that leadership in AI will confer significant economic, military, and diplomatic "
            "advantages. China's 2017 AI development plan set an explicit goal of becoming the world's "
            "leading AI power by 2030. The U.S. has responded with export controls on advanced "
            "semiconductors, restrictions on Chinese investment in AI companies, and increased "
            "federal investment in AI research.\n\n"
            "Semiconductors are the critical chokepoint. Training large AI models requires vast "
            "numbers of specialized chips, primarily designed by American companies and manufactured "
            "in Taiwan. The concentration of advanced chip fabrication in Taiwan — a flashpoint in "
            "U.S.-China tensions — represents a significant geopolitical vulnerability. The U.S. CHIPS "
            "Act of 2022 allocated $52 billion to revive domestic semiconductor manufacturing.\n\n"
            "Military applications of AI are accelerating. Autonomous weapons systems, AI-enabled "
            "surveillance, cyber operations, and battlefield decision support are being developed by "
            "major powers. This has prompted calls for international treaties governing lethal "
            "autonomous weapons, analogous to arms control agreements for nuclear and chemical "
            "weapons, though negotiations have made limited progress. The governance of AI at the "
            "international level — who sets the rules, and whether democratic and authoritarian "
            "states can agree on them — is one of the defining challenges of the coming decades."
        ),
    },
]


def upload_articles_to_s3():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )
    bucket = os.getenv("S3_BUCKET_NAME")

    for article in ARTICLES:
        filename = f"{article['id']}.txt"
        body = f"Title: {article['title']}\n\n{article['content']}"

        s3.put_object(
            Bucket=bucket,
            Key=f"articles/{filename}",
            Body=body,
            ContentType="text/plain",
        )
        print(f"Uploaded: articles/{filename}")

    print(f"\nDone. {len(ARTICLES)} articles uploaded to s3://{bucket}/articles/")


if __name__ == "__main__":
    upload_articles_to_s3()
