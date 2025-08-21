"""
Version Adapter Pattern for Cross-Version Compatibility
Handles differences between model versions to enable reproduction across versions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.config.version import ModelVersion


@dataclass
class AdaptationResult:
    """Result of version adaptation process"""
    success: bool
    adapted_config: Dict[str, Any]
    warnings: List[str]
    errors: List[str]
    adaptation_notes: List[str]


class BaseVersionAdapter(ABC):
    """Abstract base class for version adapters"""
    
    @abstractmethod
    def adapt_scenario_config(self, config: Dict[str, Any], 
                            from_version: ModelVersion, 
                            to_version: ModelVersion) -> AdaptationResult:
        """Adapt a scenario configuration between versions"""
        pass
    
    @abstractmethod
    def adapt_resolved_parameters(self, parameters: Dict[str, Any],
                                from_version: ModelVersion,
                                to_version: ModelVersion) -> AdaptationResult:
        """Adapt resolved parameter values between versions"""
        pass
    
    @abstractmethod
    def can_adapt(self, from_version: ModelVersion, to_version: ModelVersion) -> bool:
        """Check if this adapter can handle the version transition"""
        pass


class V1ToV1Adapter(BaseVersionAdapter):
    """Adapter for v1.x to v1.x transitions (patch and minor versions)"""
    
    def can_adapt(self, from_version: ModelVersion, to_version: ModelVersion) -> bool:
        """Can adapt within v1.x versions"""
        return from_version.major == 1 and to_version.major == 1
    
    def adapt_scenario_config(self, config: Dict[str, Any], 
                            from_version: ModelVersion, 
                            to_version: ModelVersion) -> AdaptationResult:
        """Adapt scenario configuration within v1.x versions"""
        
        warnings = []
        errors = []
        adaptation_notes = []
        adapted_config = config.copy()
        
        # For v1.x versions, scenario configs should be fully compatible
        if from_version != to_version:
            if from_version.minor != to_version.minor:
                warnings.append(f"Minor version difference: {from_version} -> {to_version}")
                adaptation_notes.append("Minor version differences may include new optional parameters")
            
            if from_version.patch != to_version.patch:
                adaptation_notes.append(f"Patch version difference: {from_version} -> {to_version}")
        
        return AdaptationResult(
            success=True,
            adapted_config=adapted_config,
            warnings=warnings,
            errors=errors,
            adaptation_notes=adaptation_notes
        )
    
    def adapt_resolved_parameters(self, parameters: Dict[str, Any],
                                from_version: ModelVersion,
                                to_version: ModelVersion) -> AdaptationResult:
        """Adapt resolved parameters within v1.x versions"""
        
        warnings = []
        errors = []
        adaptation_notes = []
        adapted_params = parameters.copy()
        
        # For v1.x, parameters should be compatible
        # Future v1.1+ might add new parameters, but existing ones should remain
        
        if from_version.minor < to_version.minor:
            adaptation_notes.append("Target version may include additional parameters not in original")
        elif from_version.minor > to_version.minor:
            warnings.append("Some parameters from newer version may not be available in target")
        
        return AdaptationResult(
            success=True,
            adapted_config=adapted_params,
            warnings=warnings,
            errors=errors,
            adaptation_notes=adaptation_notes
        )


class V2ToV2Adapter(BaseVersionAdapter):
    """Adapter for v2.x to v2.x transitions (patch and minor versions)"""
    
    def can_adapt(self, from_version: ModelVersion, to_version: ModelVersion) -> bool:
        """Can adapt within v2.x versions"""
        return from_version.major == 2 and to_version.major == 2
    
    def adapt_scenario_config(self, config: Dict[str, Any], 
                            from_version: ModelVersion, 
                            to_version: ModelVersion) -> AdaptationResult:
        """Adapt scenario configuration within v2.x versions"""
        
        warnings = []
        errors = []
        adaptation_notes = []
        adapted_config = config.copy()
        
        # For v2.x versions, scenario configs should be fully compatible
        if from_version != to_version:
            if from_version.minor != to_version.minor:
                warnings.append(f"Minor version difference: {from_version} -> {to_version}")
                adaptation_notes.append("Minor version differences may include new optional parameters")
            
            if from_version.patch != to_version.patch:
                adaptation_notes.append(f"Patch version difference: {from_version} -> {to_version}")
        
        return AdaptationResult(
            success=True,
            adapted_config=adapted_config,
            warnings=warnings,
            errors=errors,
            adaptation_notes=adaptation_notes
        )
    
    def adapt_resolved_parameters(self, parameters: Dict[str, Any],
                                from_version: ModelVersion,
                                to_version: ModelVersion) -> AdaptationResult:
        """Adapt resolved parameters within v2.x versions"""
        
        warnings = []
        errors = []
        adaptation_notes = []
        adapted_params = parameters.copy()
        
        # For v2.x, parameters should be compatible
        if from_version.minor < to_version.minor:
            adaptation_notes.append("Target version may include additional parameters not in original")
        elif from_version.minor > to_version.minor:
            warnings.append("Some parameters from newer version may not be available in target")
        
        return AdaptationResult(
            success=True,
            adapted_config=adapted_params,
            warnings=warnings,
            errors=errors,
            adaptation_notes=adaptation_notes
        )


class IdentityAdapter(BaseVersionAdapter):
    """Adapter for identical versions (no adaptation needed)"""
    
    def can_adapt(self, from_version: ModelVersion, to_version: ModelVersion) -> bool:
        """Can handle identical versions"""
        return from_version == to_version
    
    def adapt_scenario_config(self, config: Dict[str, Any], 
                            from_version: ModelVersion, 
                            to_version: ModelVersion) -> AdaptationResult:
        """No adaptation needed for identical versions"""
        return AdaptationResult(
            success=True,
            adapted_config=config.copy(),
            warnings=[],
            errors=[],
            adaptation_notes=["No adaptation required - identical versions"]
        )
    
    def adapt_resolved_parameters(self, parameters: Dict[str, Any],
                                from_version: ModelVersion,
                                to_version: ModelVersion) -> AdaptationResult:
        """No adaptation needed for identical versions"""
        return AdaptationResult(
            success=True,
            adapted_config=parameters.copy(),
            warnings=[],
            errors=[],
            adaptation_notes=["No adaptation required - identical versions"]
        )


class UnsupportedAdapter(BaseVersionAdapter):
    """Adapter for unsupported version transitions"""
    
    def can_adapt(self, from_version: ModelVersion, to_version: ModelVersion) -> bool:
        """Handle all other cases as unsupported"""
        return True  # Fallback adapter
    
    def adapt_scenario_config(self, config: Dict[str, Any], 
                            from_version: ModelVersion, 
                            to_version: ModelVersion) -> AdaptationResult:
        """Return failure for unsupported transitions"""
        return AdaptationResult(
            success=False,
            adapted_config={},
            warnings=[],
            errors=[f"Unsupported version transition: {from_version} -> {to_version}"],
            adaptation_notes=[
                "Major version differences require manual migration",
                "Consider upgrading reports to supported version"
            ]
        )
    
    def adapt_resolved_parameters(self, parameters: Dict[str, Any],
                                from_version: ModelVersion,
                                to_version: ModelVersion) -> AdaptationResult:
        """Return failure for unsupported transitions"""
        return AdaptationResult(
            success=False,
            adapted_config={},
            warnings=[],
            errors=[f"Unsupported version transition: {from_version} -> {to_version}"],
            adaptation_notes=[
                "Major version differences require manual migration",
                "Consider upgrading reports to supported version"
            ]
        )


class VersionAdapterRegistry:
    """Registry for managing version adapters"""
    
    def __init__(self):
        # Order matters - most specific adapters first
        self.adapters = [
            IdentityAdapter(),
            V1ToV1Adapter(),
            V2ToV2Adapter(),
            UnsupportedAdapter()  # Fallback - must be last
        ]
    
    def get_adapter(self, from_version: ModelVersion, to_version: ModelVersion) -> BaseVersionAdapter:
        """Get the appropriate adapter for a version transition"""
        for adapter in self.adapters:
            if adapter.can_adapt(from_version, to_version):
                return adapter
        
        # Should never reach here due to UnsupportedAdapter fallback
        return UnsupportedAdapter()
    
    def register_adapter(self, adapter: BaseVersionAdapter, priority: int = None):
        """Register a new adapter with optional priority"""
        if priority is None:
            # Insert before the fallback adapter
            self.adapters.insert(-1, adapter)
        else:
            self.adapters.insert(priority, adapter)


# Global adapter registry
_adapter_registry = VersionAdapterRegistry()


def get_version_adapter(from_version: ModelVersion, to_version: ModelVersion) -> BaseVersionAdapter:
    """Get the appropriate version adapter for a transition"""
    return _adapter_registry.get_adapter(from_version, to_version)


def adapt_scenario_config(config: Dict[str, Any], 
                        from_version: ModelVersion, 
                        to_version: ModelVersion) -> AdaptationResult:
    """Convenience function to adapt scenario configuration"""
    adapter = get_version_adapter(from_version, to_version)
    return adapter.adapt_scenario_config(config, from_version, to_version)


def adapt_resolved_parameters(parameters: Dict[str, Any],
                            from_version: ModelVersion,
                            to_version: ModelVersion) -> AdaptationResult:
    """Convenience function to adapt resolved parameters"""
    adapter = get_version_adapter(from_version, to_version)
    return adapter.adapt_resolved_parameters(parameters, from_version, to_version)