// Simple health check query for early app load to fail fast and surface errors
import { gql, useQuery } from "@apollo/client";

const PING = gql`
  query Ping { 
    health 
  }
`;

export function usePing() {
  return useQuery(PING, { 
    fetchPolicy: "no-cache",
    errorPolicy: "all"
  });
}
