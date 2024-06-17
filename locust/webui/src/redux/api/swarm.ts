import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

import {
  IStatsResponse,
  ISwarmExceptionsResponse,
  ISwarmRatios,
  ILogsResponse, ITotalRpsResponse, ITotalTpsResponse,
} from 'types/ui.types';
import { createFormData } from 'utils/object';
import { camelCaseKeys, snakeCaseKeys } from 'utils/string';

export const api = createApi({
  baseQuery: fetchBaseQuery(),
  endpoints: builder => ({
    getStats: builder.query<IStatsResponse, void>({
      query: () => 'stats/requests',
      transformResponse: camelCaseKeys<IStatsResponse>,
    }),
    getStatsCustom: builder.query<IStatsResponse, void>({
      query: () => 'stats_custom/requests',
      transformResponse: camelCaseKeys<IStatsResponse>,
    }),
    getTotalRps: builder.query<ITotalRpsResponse, void>({
      query: () => 'total_rps',
      transformResponse: camelCaseKeys<ITotalRpsResponse>,
    }),
    getTotalTps: builder.query<ITotalTpsResponse, void>({
      query: () => 'total_tps',
      transformResponse: camelCaseKeys<ITotalTpsResponse>,
    }),
    getTasks: builder.query<ISwarmRatios, void>({
      query: () => 'tasks',
      transformResponse: camelCaseKeys<ISwarmRatios>,
    }),
    getExceptions: builder.query<ISwarmExceptionsResponse, void>({
      query: () => 'exceptions',
      transformResponse: camelCaseKeys<ISwarmExceptionsResponse>,
    }),
    getLogs: builder.query<ILogsResponse, void>({
      query: () => 'logs',
      transformResponse: camelCaseKeys<ILogsResponse>,
    }),

    startSwarm: builder.mutation({
      query: body => ({
        url: 'swarm',
        method: 'POST',
        body: createFormData(snakeCaseKeys(body)),
        headers: { 'content-type': 'application/x-www-form-urlencoded' },
      }),
    }),
    updateUserSettings: builder.mutation({
      query: body => ({
        url: 'user',
        method: 'POST',
        body: snakeCaseKeys(body),
      }),
    }),
  }),
});

export const {
  useGetStatsQuery,
  useGetStatsCustomQuery,
  useGetTotalRpsQuery,
  useGetTotalTpsQuery,
  useGetTasksQuery,
  useGetExceptionsQuery,
  useGetLogsQuery,
  useStartSwarmMutation,
  useUpdateUserSettingsMutation,
} = api;
