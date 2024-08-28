import datetime
import time
from itertools import cycle

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.cm_import import get_different_nodes
from enmutils_int.lib.enm_export import CmExport
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CmExport11(GenericFlow):
    FILTER = ("ManagedElement.(managedElementType);Ip.(nodeIpAddress,nodeIpv6Address,nodeIpv6InterfaceName);"
              "AddressIPv6.(address);AddressIPv4.(address);ExternalENodeBFunction.(eNBId, eNodeBPlmnId);"
              "ExternalEUtranCellFDD.(eutranFrequencyRef, localCellId, physicalLayerCellIdGroup,"
              "physicalLayerSubCellId, tac, isRemoveAllowed);ExternalEUtranCellTDD.(eutranFrequencyRef,"
              "localCellId, physicalLayerCellIdGroup, physicalLayerSubCellId, tac, isRemoveAllowed);Cdma2000FreqBand.*;"
              "Cdma2000Freq.*;ExternalCdma20001xRttCell.*;"
              "InterFrequencyLoadBalancing.(featureStateInterFrequencyLoadBalancing,"
              "licenseStateInterFrequencyLoadBalancing);SectorEquipmentFunction.(rfBranchRef);RfBranch.(auPortRef);"
              "AntennaSubunit.(retSubunitRef);AntennaNearUnit.(administrativeState);RetSubUnit.(electricalAntennaTilt,"
              "maxTilt,minTilt,subunitNumber,iuantSectorId,userLabel);IpAccessHostEt.(ipAddress);ENodeBFunction.(eNBId,"
              "zzzTemporary3,upIpAddressRef,alignTtiBundWUlTrigSinr,dscpLabel,rrcConnReestActive,tRelocOverall,"
              "tS1HoCancelTimer);QciProfilePredefined.(qci,qciSubscriptionQuanta,measReportConfigParams,schedulingAlgorithm,"
              "srsAllocationStrategy,tReorderingUl);LoadBalancingFunction.(lbCeiling,lbThreshold);SectorCarrier."
              "(maximumTransmissionPower,sectorFunctionRef);EUtranCellFDD.(cellId,operationalState,earfcndl,earfcnul,"
              "isDlOnly,threshServingLow,administrativeState,tac,rachRootSequence,cellRange,pucchOverdimensioning,cellBarred,"
              "primaryPlmnReserved,qRxLevMin,dlChannelBandwidth,mobCtrlAtPoorCovActive,physicalLayerCellIdGroup,"
              "physicalLayerSubCellId,cellSubscriptionCapacity,estCellCapUsableFraction,qQualMin,qQualMinOffset,"
              "sectorCarrierRef,dummyCdmaBandClass,externalCdma20001xRttCellRef,initCdma2000SysTimeType,"
              "bccdma2000systimetype,noOfPucchCqiUsers,noOfPucchSrUsers,pZeroNominalPucch,pZeroNominalPusch,"
              "lbUtranOffloadThreshold,alpha,activePlmnList,systemInformationBlock3,systemInformationBlock6,"
              "systemInformationBlock8,mappingInfo,siPeriodicity,acBarringSkipForMmtelVideo,acBarringSkipForMmtelVoice,"
              "acBarringSkipForSms,allocThrPucchFormat1,allocTimerPucchFormat1,covTriggerdBlindHoAllowed,"
              "deallocThrPucchFormat1,deallocTimerPucchFormat1,drxActive,pdcchCovImproveDtx,"
              "pdcchCovImproveQci1,pdcchCovImproveSrb,pdcchOuterLoopInitialAdj,pdcchOuterLoopInitialAdjPCell,"
              "pdcchOuterLoopInitialAdjVolte,pdcchOuterLoopUpStep,pdcchOuterLoopUpStepPCell,pdcchOuterLoopUpStepVolte,"
              "pdcchTargetBler,pdcchTargetBlerPCell,pdcchTargetBlerVolte,ttiBundlingAfterHO,ttiBundlingAfterReest,"
              "ttiBundlingSwitchThres,ttiBundlingSwitchThresHyst);EUtranCellTDD.(cellId,operationalState,"
              "earfcn,threshServingLow,administrativeState,tac,rachRootSequence,cellRange,pucchOverdimensioning,cellBarred,"
              "primaryPlmnReserved,qRxLevMin,channelBandwidth,mobCtrlAtPoorCovActive,physicalLayerCellIdGroup,"
              "physicalLayerSubCellId,cellSubscriptionCapacity,estCellCapUsableFraction,qQualMin,qQualMinOffset,"
              "sectorCarrierRef,dummyCdmaBandClass,externalCdma20001xRttCellRef,initCdma2000SysTimeType,"
              "bccdma2000systimetype,noOfPucchCqiUsers,noOfPucchSrUsers,pZeroNominalPucch,pZeroNominalPusch,"
              "lbUtranOffloadThreshold,alpha,activePlmnList,systemInformationBlock3,systemInformationBlock6,"
              "systemInformationBlock8,mappingInfo,siPeriodicity,acBarringSkipForMmtelVideo,acBarringSkipForMmtelVoice,"
              "acBarringSkipForSms,allocThrPucchFormat1,allocTimerPucchFormat1,covTriggerdBlindHoAllowed,"
              "deallocThrPucchFormat1,deallocTimerPucchFormat1,drxActive,pdcchCovImproveDtx,pdcchCovImproveQci1,"
              "pdcchCovImproveSrb,tTimeAlignmentTimer);UeMeasControl.(a5B2MobilityTimer,ueMeasurementsActiveIF,"
              "ueMeasurementsActiveUTRAN,ueMeasurementsActiveGERAN);ReportConfigA1Prim.(a1ThresholdRsrpPrim,"
              "hysteresisA1Prim,timeToTriggerA1Prim);ReportConfigA1Sec.(a1ThresholdRsrpSec,hysteresisA1Sec,"
              "timeToTriggerA1Sec);ReportConfigA5.(a5Threshold1Rsrp,a5Threshold2Rsrp,hysteresisA5,timeToTriggerA5,"
              "triggerQuantityA5);ReportConfigA5Anr.(a5Threshold1RsrpAnrDelta,a5Threshold2RsrpAnrDelta);"
              "ReportConfigB2Utra.(b2Threshold1Rsrp,b2Threshold2RscpUtra,hysteresisB2,timeToTriggerB2,"
              "triggerQuantityB2);ReportConfigEUtraBadCovPrim.(a2ThresholdRsrpPrim,hysteresisA2Prim,timeToTriggerA2Prim,"
              "triggerQuantityA2Prim);ReportConfigEUtraBadCovSec.(a2ThresholdRsrpSec,hysteresisA2Sec,timeToTriggerA2Sec,"
              "triggerQuantityA2Sec);ReportConfigEUtraIFBestCell.(a3offset,hysteresisA3,triggerQuantityA3,"
              "timeToTriggerA3);ReportConfigEUtraBestCell.(a3offset,hysteresisA3,triggerQuantityA3,timeToTriggerA3);"
              "ReportConfigSearch.(a1a2SearchThresholdRsrp,a1a2SearchThresholdRsrq,hysteresisA1A2SearchRsrp,"
              "hysteresisA1A2SearchRsrq,timeToTriggerA1Search, timeToTriggerA2Search, a2CriticalThresholdRsrp,"
              "a2CriticalThresholdRsrq, hysteresisA2CriticalRsrp,hysteresisA2CriticalRsrq,timeToTriggerA2Critical);"
              "UtranFreqRelation.(anrMeasOn, utranFrequencyRef,pMaxUtra,csFallbackPrio,csFallbackPrioEC,"
              "mobilityActionCsfb,userLabel,cellReselectionPriority,qRxLevMin,threshXHigh,threshXLow,"
              "connectedModeMobilityPrio,qOffsetFreq,mobilityAction,qQualMin,threshXHighQ,threshXLowQ,voicePrio);"
              "EUtranFreqRelation.(eutranFrequencyRef,connectedModeMobilityPrio,qOffsetFreq,qRxLevMin,threshXLow,threshXHigh,"
              "cellReselectionPriority,interFreqMeasType,threshXHighQ,threshXLowQ,qQualMin,mobilityAction,userLabel,pMax,"
              "tReselectionEutra,tReselectionEutraSfHigh,tReselectionEutraSfMedium,allowedMeasBandwidth,presenceAntennaPort1,"
              "eutranFreqToQciProfileRelation, voicePrio, anrMeasOn, lbActivationThreshold);EUtranCellRelation.("
              "neighborCellRef,cellIndividualOffsetEUtran,qOffsetCellEUtran,loadBalancing,isHoAllowed,isRemoveAllowed, "
              "createdBy, sCellCandidate);EUtranFrequency.(arfcnValueEUtranDl);UtranFrequency.(arfcnValueUtranDl);"
              "Cdma20001xRttBandRelation.*;Cdma20001xRttFreqRelation.*;Cdma20001xRttCellRelation.*;DataRadioBearer.("
              "tPollRetransmitUl,ulMaxRetxThreshold);SignalingRadioBearer.(tPollRetransmitUl,tReorderingUl,"
              "ulMaxRetxThreshold);RlfProfile.(n310,n311,t310,t311);Rrc.(t311);Rcs.(tInactivityTimer);"
              "AutoCellCapEstFunction.(useEstimatedCellCap)")

    def calculate_the_number_of_batches(self, nodes):
        """
        Calculate the number of sets of nodes needed by the profile, based on the number of total nodes allocated. The
        profile should export 5 sets of 30 nodes if it is allocated its total number of required nodes - 150.

        :param nodes: list of nodes assigned to the profile
        :type nodes: list
        :return: num_sets: the number of sets of nodes the profile should continue with
        :rtype: int
        """
        log.logger.debug('Calculating the number of sets of nodes needed based on the number of total nodes ({0})'.format(
            len(nodes)))
        num_batches = int(len(nodes) / self.NUM_NODES_PER_BATCH)
        remaining_num_nodes = len(nodes) % self.NUM_NODES_PER_BATCH
        if remaining_num_nodes:
            log.logger.debug(
                'The number of nodes allocated to the profile does not divide evenly by the number required per set '
                '(30). One of the sets will contain only {0} nodes'.format(remaining_num_nodes))
            num_batches += 1

        return num_batches

    def create_export_objects(self, user, nodes):
        """
        Create a list of cm_export job objects. If the profile is allocated its total number of required nodes, 150,
        it should continue with 5 sets of 30 nodes. If this is not the case, we will continue with an appropriate
        number of sets based on the total number of nodes.

        :param user: user to create the cm_export job objects
        :type user: enmutils_int.lib.enm_user_2.User
        :param nodes: list of nodes for the cmexport objects
        :type nodes: list
        :return: list of cm_export_objects
        :rtype: list
        """

        cm_export_objects = []
        list_of_node_sets = []

        num_batches_needed = self.calculate_the_number_of_batches(nodes)
        nodes = get_different_nodes(nodes, self.NUM_NODES_PER_BATCH)
        for i in xrange(num_batches_needed):
            log.logger.debug('Getting nodes for node set(s) {0}/{1}'.format(i + 1, num_batches_needed))
            nodes_set = next(nodes)
            list_of_node_sets.append(nodes_set)

        nodes_cycle = cycle(list_of_node_sets)

        log.logger.debug('Creating {0} Export Objects'.format(self.NUMBER_OF_EXPORTS))
        for i in xrange(self.NUMBER_OF_EXPORTS):
            cm_export = CmExport(name='{0}_EXPORT_{1}'.format(self.identifier, i), user=user, nodes=nodes_cycle.next(),
                                 filetype=self.FILETYPE, user_filter=self.FILTER)
            cm_export_objects.append(cm_export)
        log.logger.debug('Successfully created {0} Export Objects'.format(len(cm_export_objects)))
        return cm_export_objects

    def prepare_export_lists(self, cm_export_objects):
        """
        For each job in the list of cm_export job objects, create the cm_export jobs by calling
        create_over_nbi() function

        :param cm_export_objects: cm_export job objects to create as cm_export jobs
        :type cm_export_objects: list
        :return: created_cm_export_jobs, jobs that have been created via NBI
        :rtype: list
        """
        created_cm_export_jobs = []
        for cm_export in set(cm_export_objects).symmetric_difference(created_cm_export_jobs):
            try:
                nbi_job_name = '{0}_EXPORT_{1}'.format(self.identifier, len(created_cm_export_jobs) + 1)
                log.logger.debug('Creating cm_export job {0}, export number {1}/{2}, exporting {3} total nodes.'
                                 .format(nbi_job_name, len(created_cm_export_jobs) + 1, self.NUMBER_OF_EXPORTS,
                                         len(cm_export.nodes)))
                cm_export.create_over_nbi(nbi_job_name)
                created_cm_export_jobs.append(cm_export)
                log.logger.debug('{0} CM_NBI job is created'.format(nbi_job_name))
                time.sleep(4)
            except Exception as e:
                self.add_error_as_exception(e)
                exists = cm_export.exists()
                if exists:
                    created_cm_export_jobs.append(cm_export)

        return created_cm_export_jobs

    def create_export_jobs(self, cm_export_objects):
        """
        For each job in the list of cm_export job objects, create the cm_export jobs by calling
        export_jobs_lists() function

        :param cm_export_objects: cm_export job objects to create as cm_export jobs
        :type cm_export_objects: list
        :return: created_cm_export_jobs, jobs that have been created via NBI
        :rtype: list
        """

        created_cm_export_jobs = []
        if hasattr(self, "SCHEDULED_TIMES_STRINGS"):
            timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=self.TIMEOUT)
            while datetime.datetime.now() < timeout_time and len(created_cm_export_jobs) < self.NUMBER_OF_EXPORTS:
                created_cm_export_jobs = self.prepare_export_lists(cm_export_objects)

            if len(created_cm_export_jobs) < self.NUMBER_OF_EXPORTS:
                msg = ("The profile only created {0}/{1} export jobs within "
                       "the {2}s timeout.".format(len(created_cm_export_jobs), self.NUMBER_OF_EXPORTS,
                                                  self.TIMEOUT))
                log.logger.debug(msg)
                self.add_error_as_exception(EnmApplicationError(msg))
        else:
            while len(created_cm_export_jobs) < self.NUMBER_OF_EXPORTS:
                created_cm_export_jobs = self.prepare_export_lists(cm_export_objects)

        return created_cm_export_jobs

    def validate_export_jobs(self, created_cm_export_jobs):
        """
        Validate each job in the list of cm_export jobs that have been created via NBI

        :param created_cm_export_jobs: list of cm_export jobs that have been created
        :type created_cm_export_jobs: list

        """

        for cm_export_job in created_cm_export_jobs:
            try:
                cm_export_job.validate_over_nbi()
            except Exception as e:
                self.add_error_as_exception(e)

    def execute_flow(self):
        """
        Executes the flow of cmexport_11 profile
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]

        self.state = "RUNNING"
        while self.keep_running():
            if hasattr(self, 'SCHEDULED_TIMES_STRINGS'):
                self.sleep_until_next_scheduled_iteration()
            nodes = self.get_nodes_list_by_attribute()
            if nodes:
                cm_export_objects = self.create_export_objects(user, nodes)
                created_cm_export_jobs = self.create_export_jobs(cm_export_objects)
                self.validate_export_jobs(created_cm_export_jobs)
            else:
                log.logger.debug("No nodes available to create the export job. "
                                 "Profile will continue to exchange nodes and try again on the next iteration.")
            self.exchange_nodes()
