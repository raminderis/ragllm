
'''
CREATE (u:User {username: "alice", homeCountry: "US"})
CREATE (ip:IP_Address {address: "203.0.113.5"})
CREATE (geo:GeoLocation {country: "RU"})
CREATE (d:Device {deviceId: "dev123"})
CREATE (net:NetworkSegment {segmentId: "segA", sensitivity: "high"})

CREATE (u)-[:LOGGED_IN_FROM]->(ip)
CREATE (ip)-[:BELONGS_TO]->(geo)
CREATE (u)-[:USES_DEVICE]->(d)
CREATE (d)-[:CONNECTED_TO]->(net)

CREATE (s:Session {
  sessionId: "sess001",
  startTime: datetime("2025-08-24T06:30:00"),
  endTime: datetime("2025-08-24T06:45:00"),
  status: "completed"
})

MATCH (u:User {username: "alice"}), 
      (d:Device {deviceId: "dev123"}), 
      (ip:IP_Address {address: "203.0.113.5"}), 
      (s:Session {sessionId: "sess001"})
CREATE (u)-[:INITIATED_SESSION]->(s),
       (s)-[:USED_DEVICE]->(d),
       (s)-[:FROM_IP]->(ip)
'''

import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agent import agent
import os 


from dotenv import load_dotenv
load_dotenv()


async def main():
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, session_service=session_service, app_name="network_security_app")

    session = await session_service.create_session(
        app_name="network_security_app",
        user_id="security_user",
        session_id="sec_session_001"
    )

    new_message = types.Content(role="user", parts=[types.Part(text="Scan for recent anomalies in the network graph.")])

    async for event in runner.run_async(user_id="security_user", session_id="sec_session_001", new_message=new_message):
        if event.is_final_response() and event.content and event.content.parts:
            print("\n--- Security Insight ---")
            print(event.content.parts[0].text)

if __name__ == "__main__":
    asyncio.run(main())
