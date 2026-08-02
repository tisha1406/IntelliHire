import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ProfileAPI } from "../api/profile";

export function useAdminProfile() {
    const queryClient = useQueryClient();
    
    const query = useQuery({
        queryKey: ["admin-profile"],
        queryFn: ProfileAPI.getProfile
    });

    const mutation = useMutation({
        mutationFn: ProfileAPI.updateProfile,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-profile"] });
            queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] }); // Dashboard might show welcome name
        }
    });

    return {
        ...query,
        updateProfile: mutation.mutate,
        isUpdating: mutation.isPending
    };
}
