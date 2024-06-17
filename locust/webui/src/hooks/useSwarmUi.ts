import { useEffect, useRef, useState } from 'react';

import { SWARM_STATE } from 'constants/swarm';
import useInterval from 'hooks/useInterval';
import { useGetExceptionsQuery, useGetStatsQuery, useGetStatsCustomQuery, useGetTasksQuery, useGetTotalRpsQuery, useGetTotalTpsQuery } from 'redux/api/swarm';
import { useAction, useSelector } from 'redux/hooks';
import { swarmActions } from 'redux/slice/swarm.slice';
import { uiActions } from 'redux/slice/ui.slice';
import { roundToDecimalPlaces } from 'utils/number';

const STATS_REFETCH_INTERVAL = 2000;

export default function useSwarmUi() {
  const setSwarm = useAction(swarmActions.setSwarm);
  const setUi = useAction(uiActions.setUi);
  const updateCharts = useAction(uiActions.updateCharts);
  const updateChartMarkers = useAction(uiActions.updateChartMarkers);
  const swarm = useSelector(({ swarm }) => swarm);
  const previousSwarmState = useRef(swarm.state);
  const hasSetInitStats = useRef(false);
  const [shouldAddMarker, setShouldAddMarker] = useState(false);

  const { data: totalRpsData, refetch: refetchTotalRps } = useGetTotalRpsQuery();
  const { data: totalTpsData, refetch: refetchTotalTps } = useGetTotalTpsQuery();
  const { data: statsData, refetch: refetchStats } = useGetStatsQuery();
  const { data: statsCustomData, refetch: refetchStatsCustom } = useGetStatsCustomQuery();
  const { data: tasksData, refetch: refetchTasks } = useGetTasksQuery();
  const { data: exceptionsData, refetch: refetchExceptions } = useGetExceptionsQuery();

  const shouldRunRefetchInterval =
    swarm.state === SWARM_STATE.SPAWNING || swarm.state == SWARM_STATE.RUNNING;

  const updateStatsUi = () => {
    if (!statsData) {
      return;
    }
    if (!statsCustomData) {
      return;
    }

    const {
      currentResponseTimePercentiles,
      extendedStats,
      stats,
      errors,
      totalRps,
      totalFailPerSec,
      failRatio,
      workers,
      userCount,
      totalAvgResponseTime,
    } = statsData;



    const time = new Date().toUTCString();

    if (shouldAddMarker) {
      setShouldAddMarker(false);
      updateChartMarkers(time);
    }

    const totalRpsRounded = roundToDecimalPlaces(totalRps, 2);
    const totalFailPerSecRounded = roundToDecimalPlaces(totalFailPerSec, 2);
    const totalFailureRatioRounded = roundToDecimalPlaces(failRatio * 100);

    const {
      totalTps,
    } = statsCustomData;

    const newChartEntry = {
      ...currentResponseTimePercentiles,
      currentRps: totalRpsRounded,
      currentTps: totalTps,
      currentRpsCustom: totalTps,
      currentFailPerSec: totalFailPerSecRounded,
      totalAvgResponseTime: roundToDecimalPlaces(totalAvgResponseTime, 2),
      userCount: userCount,
      time,
    };

    setUi({
      extendedStats,
      stats,
      errors,
      failRatio: totalFailureRatioRounded,
      workers,
      userCount,
    });
    updateCharts(newChartEntry);
  };

  useEffect(() => {
    if (statsData) {
      setSwarm({ state: statsData.state });
    }
  }, [statsData && statsData.state]);

  useEffect(() => {
    if (statsData) {
      if (!hasSetInitStats.current) {
        // handle setting stats on first load
        updateStatsUi();
      }

      hasSetInitStats.current = true;
    }
  }, [statsData]);

  // useEffect(() => {
  //   if (statsCustomData) {
  //       const time = new Date().toUTCString();
  //       const newChartEntry = {
  //         currentRpsCustom: statsCustomData.totalRps,
  //         currentTps: statsCustomData.totalTps,
  //         time,
  //       };
  //       updateCharts(newChartEntry);
  //   }
  // }, [statsCustomData]);

  useInterval(updateStatsUi, STATS_REFETCH_INTERVAL, {
    shouldRunInterval: !!statsData || !!statsCustomData && shouldRunRefetchInterval,
  });

  useEffect(() => {
    if (tasksData) {
      setUi({ ratios: tasksData });
    }
  }, [statsData]);

  useEffect(() => {
    if (totalRpsData) {
      setUi({ totalRps: totalRpsData.totalRps });
    }
  }, [totalRpsData]);

  useEffect(() => {
    if (totalTpsData) {
      setUi({ totalTps: totalTpsData.totalTps });
    }
  }, [totalTpsData]);

  useEffect(() => {
    if (exceptionsData) {
      setUi({ exceptions: exceptionsData.exceptions });
    }
  }, [exceptionsData]);

  useInterval(refetchTotalRps, 1000, {
    shouldRunInterval: shouldRunRefetchInterval,
  });
  useInterval(refetchTotalTps, 1000, {
    shouldRunInterval: shouldRunRefetchInterval,
  });
  useInterval(refetchStats, STATS_REFETCH_INTERVAL, {
    shouldRunInterval: shouldRunRefetchInterval,
  });
  useInterval(refetchStatsCustom, STATS_REFETCH_INTERVAL, {
    shouldRunInterval: shouldRunRefetchInterval,
  });
  useInterval(refetchTasks, 5000, {
    shouldRunInterval: shouldRunRefetchInterval,
  });
  useInterval(refetchExceptions, 5000, {
    shouldRunInterval: shouldRunRefetchInterval,
  });

  useEffect(() => {
    if (swarm.state === SWARM_STATE.RUNNING && previousSwarmState.current === SWARM_STATE.STOPPED) {
      setShouldAddMarker(true);
    }

    previousSwarmState.current = swarm.state;
  }, [swarm.state, previousSwarmState]);
}
