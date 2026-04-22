# Future work

There are several areas of interest, which could be addressed in the future. This Chapter will simply list a few.

|What can be done?|Why should it be done?|
|-|-|
|PPT: Allowing the user to manipulate Packets on a lower level|Currently, PPT only offers functionality to do rather basic en- and decryption. Having easy access to deeper packet manipulation will help users to more easily implement very obscure and creative transports|
|PPT: Allowing users to easily create authenticated Transports|Currently, PPT only implements unauthenticated transports. If such a transport is to be used realisticly, having it run in authenticated mode can help prevent active probing attacks by censors|
|PPT: Make use of the ExtORPort|Currently, PPT is only using the ORPort. This is working but it has many undesirable side effects for an actual implementation, such as the Transport not being able to authenticate to Tor and Tor not getting any information about unique connections to the PT. If this is implemented properly and correctly, the Transport should even be safe to use in security critical applications.|
|Docs: Let a beginner read over the documentation and let them restructure it/add an FAQ|The documentation is currently written with a lot of Tor-/PT-Knowledge and might at times seem chaotic or miss important information. The documentation should be reviewed by someone less experienced and restructured to better convey its information|
|Shadow: Add more thorough checks for successfull simulations|Currently, Shadow only looks at the exit states of all of its nodes and throws an error if one does not have the expected end state. This is a very good indication about weather or not everything is working as it should but in some edge cases it can gloss over a changed/undesired result. Currently manual checks are needed to determine the final state with certainty. This could be automated by reading the output files and asserting their content.|
|Shadow: Implement a proper censor|Currently the entire censorship going on in Shadow is just an edge with 100% packet loss. This is trivial to circumvent. Implementing a proper censor could increase the challenge factor for users.|
|Local and Docker Deployment: Deploy and test them in a realistic scenario on two different machines|The live deployment examples are currently all tailored for local deployment in order to demonstrate the transport. They could be deployed in a realistic scenario and their configuration could be documented to help users implement and use live PTs outside a lab setting|
